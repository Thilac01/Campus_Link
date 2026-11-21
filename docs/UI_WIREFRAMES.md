# UI Design

```text
┌────────────────────┬────────────────────────┬──────────────────────────────────────────┐
│ CampusLink         │ Workspace / list       │ Active workspace                         │
│ University space   │ [ Search ]             │ Title                                    │
│                    │                        │                                          │
│ Home               │ Overview               │ Context-specific content                 │
│ Chats              │ Recent activity        │                                          │
│ Groups             │                        │                                          │
│ Nearby Devices     │                        │                                          │
│ File Transfers     │                        │                                          │
│ …                  │                        │                                          │
│ Settings           │                        │                                          │
│                    │                        │                                          │
│ ● Local mode       │                        │                                          │
└────────────────────┴────────────────────────┴──────────────────────────────────────────┘
```

The left rail is stable navigation, the middle panel is a resizable selection context, and the
right panel is the active work surface. Phase 1 exposes Home and Settings; future items are visible
but disabled and explain their phase in a tooltip. Keyboard focus, high-DPI behavior, contrast,
and screen-reader names are release criteria. No gradient, glass, neon, or decorative animation
is used.

