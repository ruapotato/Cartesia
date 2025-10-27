"""
Modern Entity Component System for Cartesia.

Replaces the old dictionary-based entity system with proper classes,
components, and clean separation of concerns.
"""
from typing import Dict, List, Optional, Callable, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import pygame

if TYPE_CHECKING:
    from ..engine.physics import PhysicsBody


class Component(ABC):
    """Base class for all entity components."""

    def __init__(self, entity: "Entity"):
        self.entity = entity
        self.enabled = True

    @abstractmethod
    def update(self, dt: float) -> None:
        """Update this component."""
        pass


@dataclass
class TransformComponent(Component):
    """Position and orientation component."""

    x: float = 0.0
    y: float = 0.0
    rotation: float = 0.0
    scale: float = 1.0

    def __init__(self, entity: "Entity", x: float = 0, y: float = 0):
        super().__init__(entity)
        self.x = x
        self.y = y
        self.rotation = 0.0
        self.scale = 1.0

    def update(self, dt: float) -> None:
        pass  # Transform doesn't need updating

    @property
    def position(self) -> tuple[float, float]:
        return (self.x, self.y)

    @position.setter
    def position(self, pos: tuple[float, float]) -> None:
        self.x, self.y = pos


class PhysicsComponent(Component):
    """Physics and collision component."""

    def __init__(self, entity: "Entity", physics_body: "PhysicsBody"):
        super().__init__(entity)
        self.body = physics_body

    def update(self, dt: float) -> None:
        # Physics updates are handled by PhysicsEngine
        # But we sync transform with physics body
        if self.entity.has_component(TransformComponent):
            transform = self.entity.get_component(TransformComponent)
            transform.x = self.body.x
            transform.y = self.body.y


class SpriteComponent(Component):
    """Visual sprite rendering component."""

    def __init__(
        self,
        entity: "Entity",
        sprite_sheet: Optional[pygame.Surface] = None,
        sprite_size: tuple[int, int] = (64, 64)
    ):
        super().__init__(entity)
        self.sprite_sheet = sprite_sheet
        self.sprite_size = sprite_size
        self.current_frame = 0
        self.flip_x = False
        self.flip_y = False

        # Sprite sheet layout
        self.frame_width = sprite_size[0]
        self.frame_height = sprite_size[1]

    def update(self, dt: float) -> None:
        pass  # Animation component handles frame updates

    def get_current_sprite(self) -> Optional[pygame.Surface]:
        """Get the current sprite surface."""
        if not self.sprite_sheet:
            return None

        # Extract sprite from sheet
        x = (self.current_frame * self.frame_width) % self.sprite_sheet.get_width()
        y = (self.current_frame * self.frame_width) // self.sprite_sheet.get_width() * self.frame_height

        sprite = pygame.Surface((self.frame_width, self.frame_height), pygame.SRCALPHA)
        sprite.blit(self.sprite_sheet, (0, 0), (x, y, self.frame_width, self.frame_height))

        if self.flip_x or self.flip_y:
            sprite = pygame.transform.flip(sprite, self.flip_x, self.flip_y)

        return sprite


class AnimationComponent(Component):
    """Handles sprite animation."""

    def __init__(self, entity: "Entity"):
        super().__init__(entity)
        self.animations: Dict[str, Animation] = {}
        self.current_animation: Optional[str] = None
        self.animation_time = 0.0

    def add_animation(self, name: str, animation: "Animation") -> None:
        """Add a new animation."""
        self.animations[name] = animation

    def play(self, name: str, restart: bool = False) -> None:
        """Play an animation."""
        if name not in self.animations:
            return

        if self.current_animation != name or restart:
            self.current_animation = name
            self.animation_time = 0.0

    def update(self, dt: float) -> None:
        """Update animation."""
        if not self.current_animation:
            return

        anim = self.animations.get(self.current_animation)
        if not anim:
            return

        self.animation_time += dt

        # Calculate current frame
        frame_time = 1.0 / anim.fps
        frame_index = int(self.animation_time / frame_time)

        if anim.loop:
            frame_index = frame_index % len(anim.frames)
        else:
            frame_index = min(frame_index, len(anim.frames) - 1)

        # Update sprite component
        if self.entity.has_component(SpriteComponent):
            sprite = self.entity.get_component(SpriteComponent)
            sprite.current_frame = anim.frames[frame_index]


@dataclass
class Animation:
    """Animation definition."""

    frames: List[int]  # Frame indices
    fps: float = 10.0  # Frames per second
    loop: bool = True


class HealthComponent(Component):
    """Health and damage component."""

    def __init__(self, entity: "Entity", max_health: float):
        super().__init__(entity)
        self.max_health = max_health
        self.current_health = max_health
        self.invulnerable = False
        self.invulnerability_time = 0.0

    def update(self, dt: float) -> None:
        # Update invulnerability timer
        if self.invulnerable:
            self.invulnerability_time -= dt
            if self.invulnerability_time <= 0:
                self.invulnerable = False

    def damage(self, amount: float) -> bool:
        """
        Damage this entity.

        Returns True if damage was applied, False if invulnerable.
        """
        if self.invulnerable:
            return False

        self.current_health -= amount
        return True

    def heal(self, amount: float) -> None:
        """Heal this entity."""
        self.current_health = min(self.current_health + amount, self.max_health)

    def is_alive(self) -> bool:
        """Check if entity is alive."""
        return self.current_health > 0

    def set_invulnerable(self, duration: float) -> None:
        """Set temporary invulnerability."""
        self.invulnerable = True
        self.invulnerability_time = duration


class AIComponent(Component):
    """AI behavior component."""

    def __init__(self, entity: "Entity", ai_func: Optional[Callable] = None):
        super().__init__(entity)
        self.ai_function = ai_func
        self.state: Dict[str, Any] = {}

    def update(self, dt: float) -> None:
        if self.ai_function:
            self.ai_function(self.entity, dt, self.state)


class Entity:
    """
    Modern entity class with component-based architecture.

    Much cleaner than the old dictionary approach!
    """

    _next_id = 0

    def __init__(self, name: str = "Entity"):
        self.id = Entity._next_id
        Entity._next_id += 1

        self.name = name
        self.active = True
        self.tags: List[str] = []

        self._components: Dict[type, Component] = {}

    def add_component(self, component: Component) -> None:
        """Add a component to this entity."""
        component_type = type(component)
        self._components[component_type] = component

    def get_component(self, component_type: type) -> Optional[Component]:
        """Get a component by type."""
        return self._components.get(component_type)

    def has_component(self, component_type: type) -> bool:
        """Check if entity has a component."""
        return component_type in self._components

    def remove_component(self, component_type: type) -> None:
        """Remove a component."""
        if component_type in self._components:
            del self._components[component_type]

    def update(self, dt: float) -> None:
        """Update all components."""
        if not self.active:
            return

        for component in self._components.values():
            if component.enabled:
                component.update(dt)

    def add_tag(self, tag: str) -> None:
        """Add a tag to this entity."""
        if tag not in self.tags:
            self.tags.append(tag)

    def has_tag(self, tag: str) -> bool:
        """Check if entity has a tag."""
        return tag in self.tags

    def remove_tag(self, tag: str) -> None:
        """Remove a tag."""
        if tag in self.tags:
            self.tags.remove(tag)


class EntityManager:
    """
    Manages all entities in the game.

    Replaces the old NPCs list with proper entity management.
    """

    def __init__(self):
        self.entities: List[Entity] = []
        self._entities_by_tag: Dict[str, List[Entity]] = {}

    def create_entity(self, name: str = "Entity") -> Entity:
        """Create and register a new entity."""
        entity = Entity(name)
        self.entities.append(entity)
        return entity

    def add_entity(self, entity: Entity) -> None:
        """Add an existing entity."""
        if entity not in self.entities:
            self.entities.append(entity)

    def remove_entity(self, entity: Entity) -> None:
        """Remove an entity."""
        if entity in self.entities:
            self.entities.remove(entity)

            # Remove from tag cache
            for tag in entity.tags:
                if tag in self._entities_by_tag:
                    if entity in self._entities_by_tag[tag]:
                        self._entities_by_tag[tag].remove(entity)

    def get_entities_with_tag(self, tag: str) -> List[Entity]:
        """Get all entities with a specific tag."""
        return [e for e in self.entities if e.has_tag(tag)]

    def get_entities_with_component(self, component_type: type) -> List[Entity]:
        """Get all entities with a specific component."""
        return [e for e in self.entities if e.has_component(component_type)]

    def update(self, dt: float) -> None:
        """Update all entities."""
        # Create a copy to allow entities to be removed during update
        for entity in list(self.entities):
            entity.update(dt)

            # Remove dead entities
            if entity.has_component(HealthComponent):
                health = entity.get_component(HealthComponent)
                if not health.is_alive():
                    self.remove_entity(entity)

    def clear(self) -> None:
        """Remove all entities."""
        self.entities.clear()
        self._entities_by_tag.clear()
