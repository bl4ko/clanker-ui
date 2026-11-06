---
title: Avatar
description: An image element with a fallback for representing the user.
---

{{example "avatar-demo" height="18rem"}}

## Installation

Load `clanker-ui.css` and `clanker-ui.js`.

With the minified group files, load `clanker-ui-core.min.css`, `clanker-ui-layout.min.css`, and their `.min.js` files.

## Usage

```html
<span data-slot="avatar">
  <img data-slot="avatar-image" src="avatar.png" alt="@shadcn">
  <span data-slot="avatar-fallback">CN</span>
</span>
```

The fallback shows until the image loads and stays when it fails. Put the image before the fallback.

## Composition

Use the following composition to build an avatar:

```text
avatar
├── avatar-image
├── avatar-fallback
└── avatar-badge
```

Group avatars with `avatar-group`:

```text
avatar-group
├── avatar
├── avatar
└── avatar-group-count
```

## Basic

A basic avatar with an image and a fallback.

{{example "avatar-basic"}}

## Badge

Use `avatar-badge` to add a badge to the avatar. The badge is at the bottom right of the avatar.

Use classes or app CSS to change the badge, for example its color or size.

```html
<span data-slot="avatar">
  <img data-slot="avatar-image" src="avatar.png" alt="@shadcn">
  <span data-slot="avatar-fallback">CN</span>
  <span data-slot="avatar-badge" class="bg-green-600 dark:bg-green-800"></span>
</span>
```

{{example "avatar-badge"}}

## Badge with Icon

You can also put an icon in `avatar-badge`.

{{example "avatar-badge-icon"}}

## Avatar Group

Use `avatar-group` to show a group of avatars.

{{example "avatar-group"}}

## Avatar Group Count

Use `avatar-group-count` to add a count to the group.

{{example "avatar-group-count"}}

## Avatar Group with Icon

You can also put an icon in `avatar-group-count`.

{{example "avatar-group-count-icon"}}

## Sizes

Use `data-size` to change the size of the avatar.

{{example "avatar-size"}}

## Dropdown

You can use an avatar as the trigger of a [Dropdown Menu](/docs/components/dropdown-menu).

{{example "avatar-dropdown"}}

## RTL

The avatar uses logical properties: the badge and the group overlap follow the direction. Set `dir="rtl"` on `<html>` or on a container. See [Direction](/docs/components/direction).

{{example "avatar-rtl" height="18rem"}}

## API Reference

### Avatar

| Attribute | Values | Default |
| --- | --- | --- |
| `data-size` | `"default" \| "sm" \| "lg"` | `"default"` |

### Avatar Image

An `<img>` with `src` and `alt`. The kit sets `data-status="loading|loaded|error"`.

### Avatar Fallback

The text or icon that shows while the image loads or when it fails. The kit hides the image or the fallback with `visibility: hidden`.

### Avatar Badge

A badge at the bottom right of the avatar (bottom left in RTL).

### Avatar Group

A row of avatars that overlap.

### Avatar Group Count

The count at the end of a group, for example `+3` or an icon.
