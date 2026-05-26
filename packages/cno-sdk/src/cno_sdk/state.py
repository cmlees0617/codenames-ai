"""Typed helpers for parsing codenames.game boardgame.io state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

TeamColor = Literal["red", "blue"]
Role = Literal["operatives", "spymasters"]
CardColor = Literal["red", "blue", "neutral", "black"]


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
    raw: dict[str, Any] = field(repr=False, default_factory=dict)

    @classmethod
    def from_bgio(cls, state: dict[str, Any]) -> GameState:
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
            raw=state,
        )


def player_key(player_id: str) -> str:
    return f"p#{player_id}"


def is_seated(state: GameState, player_id: str, team: TeamColor, role: Role) -> bool:
    slot = state.teams.get(team, {}).get(role, {})
    return player_key(player_id) in slot


def is_spymaster_turn(state: GameState, player_id: str, team: TeamColor) -> bool:
    return (
        state.cards_dealed
        and state.gameover is None
        and state.active_team == team
        and state.active_role == "spymasters"
        and is_seated(state, player_id, team, "spymasters")
    )


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
