# UI_DESIGN_SYSTEM

> **Purpose**: Document the visual language, aesthetics, and interaction philosophy.
> **Scope**: Design tokens, styles, and UI guidelines.
> **Last Updated**: 2026-07-13
> **Related Documents**: [FRONTEND_ARCHITECTURE.md](./FRONTEND_ARCHITECTURE.md), [COMPONENT_GUIDE.md](./COMPONENT_GUIDE.md)

## Quick Summary
FRIDAY's design language is "Apple × Iron Man × Interstellar." It focuses on dark modes, glassmorphism, fluid micro-animations, and high-end typography to create a premium, alive interface.

## Design Philosophy
1. **Dynamic Design**: The interface must feel alive. Hover effects, subtle breathing animations, and state transitions are mandatory.
2. **Premium Feel**: Avoid flat, generic colors. Use deep blacks, subtle glowing accents, and high-contrast typography.
3. **Unobtrusive**: The UI should get out of the way of the conversation.

## Typography
- **Primary Font**: `Inter` or `SF Pro` (clean, modern, highly legible).
- **Secondary Font**: `Outfit` or `Space Grotesk` (for futuristic accents or numbers).
- **Hierarchy**: Strict use of weights (Light for descriptions, Medium for body, Semibold for headers).

## Color Palette
- **Background**: Deep space black (`#050505`) with subtle radial gradients for depth.
- **Primary Accent**: Cyan/Blue glow (`#00F0FF`) representing active states.
- **Secondary Accent**: Warm amber (`#FFB000`) for warnings or specific insights.
- **Surfaces**: Translucent dark layers (`rgba(255, 255, 255, 0.03)`) for glass effects.

## Spacing & Layout
- Use an 8px grid system.
- High padding and margins to let components breathe.

## Animations & Motion Principles
- **Spring Physics**: Avoid linear CSS transitions. Use spring physics for natural, fluid motion.
- **State Indicators**: The Orb is the primary visual anchor. Its animation dictates the system's state:
  - *Idle*: Slow, organic breathing.
  - *Listening*: Reactive to audio input frequencies.
  - *Thinking*: Fast, constrained spinning or pulsing.
  - *Speaking*: Smooth waveforms or expanding rings.

## Component Philosophy
- **Glassmorphism**: Modals and cards should feature background-blur, thin subtle borders (`1px solid rgba(255,255,255,0.1)`), and drop shadows for elevation.
- **Icons**: Minimalist, stroked icons (e.g., Lucide or Phosphor). No filled, heavy icons unless indicating an active toggle.
