"""
Inventory and item system for Cartesia.

Starbound-style inventory with:
- Hotbar (quick access)
- Main inventory
- Item stacking
- Drag and drop
- Tool durability
"""
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pygame


class ItemType(Enum):
    """Types of items."""
    BLOCK = "block"
    TOOL = "tool"
    WEAPON = "weapon"
    CONSUMABLE = "consumable"
    MATERIAL = "material"
    SEED = "seed"


class ToolType(Enum):
    """Types of tools."""
    PICKAXE = "pickaxe"
    AXE = "axe"
    SHOVEL = "shovel"
    HOE = "hoe"
    SWORD = "sword"
    BOW = "bow"


@dataclass
class ItemDefinition:
    """Defines an item type."""

    id: str
    name: str
    item_type: ItemType
    max_stack: int = 99
    tool_type: Optional[ToolType] = None
    tool_power: int = 1  # Mining/chopping power
    max_durability: int = 0  # 0 = infinite
    icon_path: Optional[str] = None
    icon: Optional[pygame.Surface] = None
    placeable_block_id: Optional[int] = None  # Block ID if this item can be placed

    def __post_init__(self):
        """Load icon if path provided."""
        if self.icon_path and not self.icon:
            try:
                self.icon = pygame.image.load(self.icon_path).convert_alpha()
            except:
                pass


@dataclass
class ItemStack:
    """A stack of items in inventory."""

    item_id: str
    quantity: int = 1
    durability: int = 0  # For tools

    def can_stack_with(self, other: "ItemStack", item_def: ItemDefinition) -> bool:
        """Check if this stack can combine with another."""
        if self.item_id != other.item_id:
            return False
        if item_def.max_durability > 0:
            return False  # Tools don't stack
        return self.quantity + other.quantity <= item_def.max_stack

    def stack_with(self, other: "ItemStack", item_def: ItemDefinition) -> Optional["ItemStack"]:
        """
        Combine with another stack.

        Returns the remainder if any.
        """
        if not self.can_stack_with(other, item_def):
            return other

        total = self.quantity + other.quantity
        if total <= item_def.max_stack:
            self.quantity = total
            return None
        else:
            self.quantity = item_def.max_stack
            other.quantity = total - item_def.max_stack
            return other

    def split(self, amount: int) -> Optional["ItemStack"]:
        """Split stack, returning the split portion."""
        if amount >= self.quantity:
            result = ItemStack(self.item_id, self.quantity, self.durability)
            self.quantity = 0
            return result
        else:
            self.quantity -= amount
            return ItemStack(self.item_id, amount, self.durability)


class ItemRegistry:
    """Central registry for all item types."""

    def __init__(self):
        self.items: Dict[str, ItemDefinition] = {}
        self._register_default_items()

    def _register_default_items(self):
        """Register default game items."""
        # Tools
        self.register(ItemDefinition(
            id="pickaxe_wood",
            name="Wooden Pickaxe",
            item_type=ItemType.TOOL,
            tool_type=ToolType.PICKAXE,
            tool_power=1,
            max_durability=60,
            max_stack=1,
            icon_path="img/pixelperfection/default/default_tool_woodpick.png"
        ))

        self.register(ItemDefinition(
            id="pickaxe_stone",
            name="Stone Pickaxe",
            item_type=ItemType.TOOL,
            tool_type=ToolType.PICKAXE,
            tool_power=2,
            max_durability=120,
            max_stack=1,
            icon_path="img/pixelperfection/default/default_tool_stonepick.png"
        ))

        self.register(ItemDefinition(
            id="axe_wood",
            name="Wooden Axe",
            item_type=ItemType.TOOL,
            tool_type=ToolType.AXE,
            tool_power=1,
            max_durability=60,
            max_stack=1,
            icon_path="img/pixelperfection/default/default_tool_woodaxe.png"
        ))

        self.register(ItemDefinition(
            id="shovel_wood",
            name="Wooden Shovel",
            item_type=ItemType.TOOL,
            tool_type=ToolType.SHOVEL,
            tool_power=1,
            max_durability=60,
            max_stack=1,
            icon_path="img/pixelperfection/default/default_tool_woodshovel.png"
        ))

        self.register(ItemDefinition(
            id="hoe_wood",
            name="Wooden Hoe",
            item_type=ItemType.TOOL,
            tool_type=ToolType.HOE,
            tool_power=1,
            max_durability=60,
            max_stack=1,
            icon_path="img/pixelperfection/farming/farming_tool_woodhoe.png"
        ))

        # Blocks (placeable)
        self.register(ItemDefinition(
            id="dirt",
            name="Dirt",
            item_type=ItemType.BLOCK,
            max_stack=999,
            placeable_block_id=3,
            icon_path="img/pixelperfection/default/default_dirt.png"
        ))

        self.register(ItemDefinition(
            id="stone",
            name="Stone",
            item_type=ItemType.BLOCK,
            max_stack=999,
            placeable_block_id=4,
            icon_path="img/pixelperfection/default/default_stone.png"
        ))

        self.register(ItemDefinition(
            id="torch",
            name="Torch",
            item_type=ItemType.BLOCK,
            max_stack=99,
            placeable_block_id=5,
            icon_path="img/pixelperfection/default/default_torch.png"
        ))

        # Seeds
        self.register(ItemDefinition(
            id="wheat_seed",
            name="Wheat Seeds",
            item_type=ItemType.SEED,
            max_stack=99,
            icon_path="img/pixelperfection/farming/farming_wheat_seed.png"
        ))

        # Materials
        self.register(ItemDefinition(
            id="wheat",
            name="Wheat",
            item_type=ItemType.MATERIAL,
            max_stack=99,
            icon_path="img/pixelperfection/farming/farming_wheat.png"
        ))

        self.register(ItemDefinition(
            id="flour",
            name="Flour",
            item_type=ItemType.MATERIAL,
            max_stack=99,
            icon_path="img/pixelperfection/farming/farming_flour.png"
        ))

        # Food
        self.register(ItemDefinition(
            id="bread",
            name="Bread",
            item_type=ItemType.CONSUMABLE,
            max_stack=99,
            icon_path="img/pixelperfection/farming/farming_bread.png"
        ))

    def register(self, item: ItemDefinition):
        """Register an item definition."""
        self.items[item.id] = item

    def get(self, item_id: str) -> Optional[ItemDefinition]:
        """Get an item definition."""
        return self.items.get(item_id)


class Inventory:
    """
    Player inventory with hotbar and main storage.

    Starbound-style inventory system!
    """

    def __init__(self, hotbar_size: int = 9, rows: int = 4, cols: int = 9):
        self.hotbar_size = hotbar_size
        self.rows = rows
        self.cols = cols

        # Inventory slots (None = empty)
        self.hotbar: List[Optional[ItemStack]] = [None] * hotbar_size
        self.main: List[Optional[ItemStack]] = [None] * (rows * cols)

        # Selected hotbar slot
        self.selected_slot = 0

        # Item registry
        self.registry = ItemRegistry()

    def get_selected_item(self) -> Optional[ItemStack]:
        """Get the currently selected item."""
        return self.hotbar[self.selected_slot]

    def get_selected_item_def(self) -> Optional[ItemDefinition]:
        """Get the definition of the selected item."""
        item = self.get_selected_item()
        if not item:
            return None
        return self.registry.get(item.item_id)

    def add_item(self, item_id: str, quantity: int = 1) -> int:
        """
        Add items to inventory.

        Returns the number of items that couldn't be added.
        """
        item_def = self.registry.get(item_id)
        if not item_def:
            return quantity

        remaining = quantity

        # Try to stack with existing items
        for slot in self.hotbar + self.main:
            if slot and slot.item_id == item_id and remaining > 0:
                can_add = min(remaining, item_def.max_stack - slot.quantity)
                slot.quantity += can_add
                remaining -= can_add

        # Add to empty slots
        if remaining > 0:
            for i, slot in enumerate(self.hotbar):
                if not slot and remaining > 0:
                    add_amount = min(remaining, item_def.max_stack)
                    self.hotbar[i] = ItemStack(item_id, add_amount)
                    remaining -= add_amount

        if remaining > 0:
            for i, slot in enumerate(self.main):
                if not slot and remaining > 0:
                    add_amount = min(remaining, item_def.max_stack)
                    self.main[i] = ItemStack(item_id, add_amount)
                    remaining -= add_amount

        return remaining

    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        """
        Remove items from inventory.

        Returns True if successful, False if not enough items.
        """
        # Count how many we have
        total = self.count_item(item_id)
        if total < quantity:
            return False

        # Remove from slots
        remaining = quantity
        for slot in self.hotbar + self.main:
            if slot and slot.item_id == item_id and remaining > 0:
                remove_amount = min(remaining, slot.quantity)
                slot.quantity -= remove_amount
                remaining -= remove_amount

                if slot.quantity == 0:
                    # Clear empty slot
                    if slot in self.hotbar:
                        self.hotbar[self.hotbar.index(slot)] = None
                    else:
                        self.main[self.main.index(slot)] = None

        return True

    def count_item(self, item_id: str) -> int:
        """Count how many of an item we have."""
        total = 0
        for slot in self.hotbar + self.main:
            if slot and slot.item_id == item_id:
                total += slot.quantity
        return total

    def has_item(self, item_id: str, quantity: int = 1) -> bool:
        """Check if we have enough of an item."""
        return self.count_item(item_id) >= quantity

    def damage_selected_tool(self, amount: int = 1) -> bool:
        """
        Damage the selected tool.

        Returns True if tool broke.
        """
        item = self.get_selected_item()
        if not item:
            return False

        item_def = self.registry.get(item.item_id)
        if not item_def or item_def.max_durability == 0:
            return False

        item.durability += amount

        if item.durability >= item_def.max_durability:
            # Tool broke!
            self.hotbar[self.selected_slot] = None
            return True

        return False


# Global item registry
_item_registry: Optional[ItemRegistry] = None


def get_item_registry() -> ItemRegistry:
    """Get the global item registry."""
    global _item_registry
    if _item_registry is None:
        _item_registry = ItemRegistry()
    return _item_registry
