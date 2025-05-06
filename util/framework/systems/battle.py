import asyncio
import random
from enum import Enum, auto
from typing import Dict, List, Optional

from util.framework.globals import G
from util.framework.core.interactors.interactor import Interactor, BaseInteraction
from util.framework.core.interactors.intBase import IOnEncounterStart, IOnEncounterEnd


class ElementType(Enum):
    ROCK = auto()
    PAPER = auto()
    SCISSORS = auto()


class ActionType(Enum):
    ATTACK = auto()
    DEFEND = auto()
    SKILL = auto()
    ITEM = auto()
    ESCAPE = auto()


class BattleState(Enum):
    IDLE = auto()
    BATTLE_START = auto()
    PLAYER_TURN = auto()
    ENEMY_TURN = auto()
    BATTLE_END = auto()


class BattleResult(Enum):
    NONE = auto()
    VICTORY = auto()
    DEFEAT = auto()
    ESCAPE = auto()


class BattleAction:
    def __init__(self, name: str, action_type: ActionType, element: ElementType, power: int = 10):
        self.name = name
        self.action_type = action_type
        self.element = element
        self.power = power


class BattleEntity:
    def __init__(self, name: str, hp: int = 100, is_player: bool = False):
        self.name = name
        self.max_hp = hp
        self.current_hp = hp
        self.is_player = is_player
        self.element = None
        self.actions = []
        self.setup_actions()

    def setup_actions(self):
        self.actions = [
            BattleAction("Rock Smash", ActionType.ATTACK, ElementType.ROCK, 15),
            BattleAction("Paper Cut", ActionType.ATTACK, ElementType.PAPER, 15),
            BattleAction("Scissor Slash", ActionType.ATTACK, ElementType.SCISSORS, 15),
            BattleAction("Defend", ActionType.DEFEND, random.choice(list(ElementType)), 0),
            BattleAction("Escape", ActionType.ESCAPE, random.choice(list(ElementType)), 0)
        ]

    @property
    def is_alive(self) -> bool:
        return self.current_hp > 0

    def take_damage(self, amount: int) -> int:
        actual_damage = min(self.current_hp, max(1, amount))
        self.current_hp -= actual_damage
        return actual_damage

    def heal(self, amount: int) -> int:
        missing_hp = self.max_hp - self.current_hp
        actual_healing = min(missing_hp, amount)
        self.current_hp += actual_healing
        return actual_healing


class BattleStartInteraction(BaseInteraction, IOnEncounterStart):
    def __init__(self):
        super().__init__()

    def priority(self) -> int:
        return -100

    async def on_encounter_start(self, args=None):
        battle_system = G.im.get_interactor('BattleSystem')
        if battle_system:
            await battle_system.initialize_battle(args)


class BattleEndInteraction(BaseInteraction, IOnEncounterEnd):
    def __init__(self):
        super().__init__()

    def priority(self) -> int:
        return 100

    async def on_encounter_end(self, args=None):
        battle_system = G.im.get_interactor('BattleSystem')
        if battle_system:
            await battle_system.cleanup_battle(args)


class BattleSystem(Interactor):
    def __init__(self):
        super().__init__()
        self.state = BattleState.IDLE
        self.result = BattleResult.NONE
        self.turn_count = 0

        self.player = None
        self.enemies = []

        self.current_entity = None
        self.current_action = None
        self.current_target = None

        self.is_defending = False
        self.battle_delay = 0.5
        self._coroutine_battle_loop = None

        self.element_advantages = {
            ElementType.ROCK: ElementType.SCISSORS,
            ElementType.PAPER: ElementType.ROCK,
            ElementType.SCISSORS: ElementType.PAPER
        }

    def awake(self):
        super().awake()
        self.add_interaction(BattleStartInteraction())
        self.add_interaction(BattleEndInteraction())

    async def initialize_battle(self, encounter_data=None):
        self.state = BattleState.IDLE
        self.result = BattleResult.NONE
        self.turn_count = 0
        self.enemies.clear()

        player_entity = G.object_collections.find_first('entities', lambda e: hasattr(e, 'is_player') and e.is_player)
        if player_entity:
            self.player = BattleEntity(player_entity.name, 100, True)
        else:
            self.player = BattleEntity("Player", 100, True)

        if encounter_data:
            if isinstance(encounter_data, list):
                for enemy_data in encounter_data:
                    name = enemy_data.get('name', 'Enemy')
                    hp = enemy_data.get('hp', 100)
                    enemy = BattleEntity(name, hp, False)
                    self.enemies.append(enemy)
            elif isinstance(encounter_data, dict):
                name = encounter_data.get('name', 'Enemy')
                hp = encounter_data.get('hp', 100)
                enemy = BattleEntity(name, hp, False)
                self.enemies.append(enemy)

        if not self.enemies:
            self.enemies.append(BattleEntity("Enemy", 100, False))

        print(f"Battle starting against {len(self.enemies)} enemies!")

        self.state = BattleState.BATTLE_START
        self._coroutine_battle_loop = self.start_coroutine(self.battle_loop())

    async def cleanup_battle(self, args=None):
        if self._coroutine_battle_loop:
            self.stop_coroutine(self._coroutine_battle_loop)
            self._coroutine_battle_loop = None

        self.state = BattleState.IDLE
        self.player = None
        self.enemies.clear()

    async def battle_loop(self):
        await self.wait_for_seconds(self.battle_delay)
        print("Battle started!")

        while self.state != BattleState.BATTLE_END:
            if self.state == BattleState.BATTLE_START:
                self.turn_count += 1
                print(f"\n--- Turn {self.turn_count} ---")
                self.state = BattleState.PLAYER_TURN

            elif self.state == BattleState.PLAYER_TURN:
                await self.handle_player_turn()

                if self.check_battle_end():
                    self.state = BattleState.BATTLE_END
                else:
                    self.state = BattleState.ENEMY_TURN

            elif self.state == BattleState.ENEMY_TURN:
                await self.handle_enemy_turns()

                if self.check_battle_end():
                    self.state = BattleState.BATTLE_END
                else:
                    self.state = BattleState.BATTLE_START

            await self.wait_for_seconds(0.05)

        await self.end_battle()

    async def handle_player_turn(self):
        if not self.player.is_alive:
            return

        print(f"\n{self.player.name}'s turn")
        print(f"HP: {self.player.current_hp}/{self.player.max_hp}")
        print("Choose an action:")

        for i, action in enumerate(self.player.actions):
            print(f"{i + 1}. {action.name}")

        await self.wait_for_seconds(self.battle_delay)

        action_index = 0
        self.current_action = self.player.actions[action_index]
        print(f"Selected: {self.current_action.name}")

        if self.current_action.action_type == ActionType.ESCAPE:
            escape_chance = 0.5
            if random.random() < escape_chance:
                print("Escaped successfully!")
                self.result = BattleResult.ESCAPE
                self.state = BattleState.BATTLE_END
                return
            else:
                print("Failed to escape!")
                return

        if self.current_action.action_type == ActionType.DEFEND:
            self.is_defending = True
            print(f"{self.player.name} is defending!")
            return

        if len(self.enemies) > 0:
            print("Choose a target:")
            for i, enemy in enumerate(self.enemies):
                if enemy.is_alive:
                    print(f"{i + 1}. {enemy.name} - HP: {enemy.current_hp}/{enemy.max_hp}")

            target_index = 0
            self.current_target = self.enemies[target_index]
            print(f"Targeting: {self.current_target.name}")

            await self.execute_action(self.player, self.current_target, self.current_action)

    async def handle_enemy_turns(self):
        for enemy in self.enemies:
            if enemy.is_alive:
                print(f"\n{enemy.name}'s turn")

                attack_actions = [a for a in enemy.actions if a.action_type == ActionType.ATTACK]
                if attack_actions:
                    action = random.choice(attack_actions)
                    print(f"{enemy.name} uses {action.name}!")

                    await self.execute_action(enemy, self.player, action)

                    if not self.player.is_alive:
                        break

                await self.wait_for_seconds(self.battle_delay)

    async def execute_action(self, attacker, defender, action):
        if action.action_type == ActionType.ATTACK:
            base_damage = action.power

            attacker_element = action.element
            defender_element = defender.element if defender.element else random.choice(list(ElementType))

            element_multiplier = self.calculate_element_bonus(attacker_element, defender_element)

            if defender == self.player and self.is_defending:
                defense_multiplier = 0.5
                self.is_defending = False
            else:
                defense_multiplier = 1.0

            final_damage = int(base_damage * element_multiplier * defense_multiplier)

            if element_multiplier > 1:
                print(f"It's super effective! ({attacker_element.name} > {defender_element.name})")
            elif element_multiplier < 1:
                print(f"It's not very effective... ({attacker_element.name} < {defender_element.name})")

            actual_damage = defender.take_damage(final_damage)
            print(f"{defender.name} takes {actual_damage} damage!")

            if not defender.is_alive:
                print(f"{defender.name} was defeated!")

        await self.wait_for_seconds(self.battle_delay)

    def calculate_element_bonus(self, attacker_element, defender_element):
        if attacker_element == defender_element:
            return 1.0
        elif self.element_advantages[attacker_element] == defender_element:
            return 1.5
        else:
            return 0.75

    def check_battle_end(self) -> bool:
        if not self.player.is_alive:
            self.result = BattleResult.DEFEAT
            return True

        enemies_alive = any(enemy.is_alive for enemy in self.enemies)
        if not enemies_alive:
            self.result = BattleResult.VICTORY
            return True

        return False

    async def end_battle(self):
        if self.result == BattleResult.VICTORY:
            print("\nVictory!")

            xp_reward = 20 * len(self.enemies)
            gold_reward = random.randint(10, 30) * len(self.enemies)
            print(f"Gained {xp_reward} XP and {gold_reward} gold!")

        elif self.result == BattleResult.DEFEAT:
            print("\nDefeat!")

        elif self.result == BattleResult.ESCAPE:
            print("\nEscaped from battle!")

        await self.wait_for_seconds(self.battle_delay)
        print("\nBattle ended!")

        self.state = BattleState.IDLE