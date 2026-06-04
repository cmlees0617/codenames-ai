"""Typed helpers for parsing codenames.game boardgame.io state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

# Keep in sync with game_core.types (same literals; SDK does not depend on game-core).
TeamColor = Literal["red", "blue"]
Role = Literal["operatives", "spymasters"]
CardColor = Literal["red", "blue", "neutral", "black"]
TileColor = Literal["red", "blue", "civilian", "assassin"]


def card_color_to_tile(color: CardColor) -> TileColor:
    if color == "black":
        return "assassin"
    if color == "neutral":
        return "civilian"
    return color


@dataclass
class BoardCard:
    index: int
    word: str
    color: CardColor
    revealed: bool = False
    selected: bool = False
    tips: dict[str, bool] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BoardCard:
        return cls(
            index=int(data.get("index", 0)),
            word=str(data["word"]).upper(),
            color=data["color"],
            revealed=bool(data.get("revealed", False)),
            selected=bool(data.get("selected", False)),
            tips=dict(data.get("tips") or {}),
        )

    @property
    def tile_color(self) -> TileColor:
        return card_color_to_tile(self.color)


@dataclass
class BoardTile:
    index: int
    word: str
    color: TileColor
    revealed: bool

    @classmethod
    def from_card(cls, card: BoardCard) -> BoardTile:
        return cls(
            index=card.index,
            word=card.word,
            color=card.tile_color,
            revealed=card.revealed,
        )


@dataclass
class ClueRecord:
    word: str
    count: int
    team: TeamColor | None = None
    spymaster_id: str | None = None
    selected_words: list[str] = field(default_factory=list)


@dataclass
class GuessRecord:
    word: str
    card_color: TileColor
    team: TeamColor | None = None
    player_id: str | None = None
    player_name: str | None = None


@dataclass
class GameView:
    """Structured snapshot of the current game."""

    phase: str | None
    cards_dealed: bool
    active_team: TeamColor | None
    active_role: Role | None
    gameover: str | None
    board: list[BoardTile]
    clues: list[ClueRecord]
    guesses: list[GuessRecord]

    @property
    def unrevealed_friendly(self) -> dict[TeamColor, list[str]]:
        result: dict[TeamColor, list[str]] = {"red": [], "blue": []}
        for tile in self.board:
            if not tile.revealed and tile.color in ("red", "blue"):
                result[tile.color].append(tile.word)
        return result


@dataclass
class GameState:
    state_id: int
    grid: list[BoardCard]
    active_team: TeamColor | None
    active_role: Role | None
    cards_dealed: bool
    gameover: str | None
    guess_limit: int | None
    teams: dict[str, dict[str, dict[str, bool]]]
    phase: str | None
    current_player: str | None
    log: list[dict[str, Any]] = field(repr=False, default_factory=list)
    raw: dict[str, Any] = field(repr=False, default_factory=dict)

    @classmethod
    def from_bgio(
        cls,
        state: dict[str, Any],
        *,
        log: list[dict[str, Any]] | None = None,
    ) -> GameState:
        g = state.get("G") or {}
        ctx = state.get("ctx") or {}
        grid = [BoardCard.from_dict(card) for card in g.get("grid") or []]
        return cls(
            state_id=int(state.get("_stateID", 0)),
            grid=grid,
            active_team=g.get("activeTeam"),
            active_role=g.get("activeRole"),
            cards_dealed=bool(g.get("cardsDealed")),
            gameover=g.get("gameover"),
            guess_limit=g.get("guessLimit"),
            teams=g.get("teams") or {},
            phase=ctx.get("phase"),
            current_player=ctx.get("currentPlayer"),
            log=list(log or []),
            raw=state,
        )

    def to_view(self) -> GameView:
        return GameView(
            phase=self.phase,
            cards_dealed=self.cards_dealed,
            active_team=self.active_team,
            active_role=self.active_role,
            gameover=self.gameover,
            board=[BoardTile.from_card(card) for card in self.grid],
            clues=parse_clues(self.log),
            guesses=parse_guesses(self.log),
        )


def player_key(player_id: str) -> str:
    return f"p#{player_id}"


def is_seated(state: GameState, player_id: str, team: TeamColor, role: Role) -> bool:
    slot = state.teams.get(team, {}).get(role, {})
    return player_key(player_id) in slot


def is_seated_anywhere(state: GameState, player_id: str) -> bool:
    key = player_key(player_id)
    for team in state.teams.values():
        for role in team.values():
            if key in role:
                return True
    return False


def is_spymaster_turn(state: GameState, player_id: str, team: TeamColor) -> bool:
    return (
        state.cards_dealed
        and state.gameover is None
        and state.active_team == team
        and state.active_role == "spymasters"
        and is_seated(state, player_id, team, "spymasters")
    )


def is_operative_turn(state: GameState, player_id: str, team: TeamColor) -> bool:
    return (
        state.cards_dealed
        and state.gameover is None
        and state.active_team == team
        and state.active_role == "operatives"
        and is_seated(state, player_id, team, "operatives")
        and (state.guess_limit or 0) > 0
    )


def unrevealed_cards(state: GameState) -> list[BoardCard]:
    return [card for card in state.grid if not card.revealed]


def friendly_unrevealed(state: GameState, team: TeamColor) -> list[BoardCard]:
    return [
        card
        for card in state.grid
        if card.color == team and not card.revealed
    ]


def pick_friendly_words(
    state: GameState,
    team: TeamColor,
    preferred: list[str],
    count: int,
) -> list[str]:
    by_word = {card.word: card for card in state.grid}
    selected: list[str] = []
    for word in preferred:
        card = by_word.get(word.upper())
        if card and card.color == team and not card.revealed:
            selected.append(card.word)
        if len(selected) >= count:
            return selected[:count]

    for card in friendly_unrevealed(state, team):
        if card.word not in selected:
            selected.append(card.word)
        if len(selected) >= count:
            break

    if len(selected) < count:
        raise ValueError(
            f"Need {count} unrevealed {team} cards, found {len(selected)}"
        )
    return selected[:count]


def _move_payload(entry: dict[str, Any]) -> dict[str, Any] | None:
    action = entry.get("action") or {}
    payload = action.get("payload")
    return payload if isinstance(payload, dict) else None


def parse_clues(log: list[dict[str, Any]]) -> list[ClueRecord]:
    clues: list[ClueRecord] = []
    for entry in log:
        payload = _move_payload(entry)
        if not payload or payload.get("type") != "giveClue":
            continue
        args = payload.get("args") or []
        if not args:
            continue
        clue = args[0] if isinstance(args[0], dict) else {}
        selected = args[2] if len(args) > 2 and isinstance(args[2], list) else []
        number = clue.get("number")
        clues.append(
            ClueRecord(
                word=str(clue.get("word", "")).upper(),
                count=int(number) if number is not None else len(selected),
                spymaster_id=str(payload.get("playerID"))
                if payload.get("playerID") is not None
                else None,
                selected_words=[str(word).upper() for word in selected],
            )
        )
    return clues


def parse_guesses(log: list[dict[str, Any]]) -> list[GuessRecord]:
    guesses: list[GuessRecord] = []
    for entry in log:
        payload = _move_payload(entry)
        if not payload or payload.get("type") != "guessCard":
            continue
        args = payload.get("args") or []
        if not args:
            continue
        word = str(args[0]).upper()
        meta = args[1] if len(args) > 1 and isinstance(args[1], dict) else {}
        card_color = meta.get("cardColor", "neutral")
        tile_color = card_color_to_tile(card_color)
        guesses.append(
            GuessRecord(
                word=word,
                card_color=tile_color,
                team=meta.get("playerTeam"),
                player_id=str(meta.get("playerID"))
                if meta.get("playerID") is not None
                else str(payload.get("playerID"))
                if payload.get("playerID") is not None
                else None,
                player_name=meta.get("playerName"),
            )
        )
    return guesses
