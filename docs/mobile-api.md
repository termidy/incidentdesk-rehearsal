# Mobile API

The mobile API is available under `/mobile/v1`.

## `GET /mobile/v1/incidents`

Returns open (non-resolved) incidents, newest first, in pages of 20.

**Request:** Optional query parameter `page` (integer, default `1`; must be at
least `1`).

**Success (`200`):** An object with `items` and `next_page`. Each item contains
`key`, `title`, `service`, `priority`, `status`, and `opened_at`. `next_page`
is the next page number, or `null` on the last page.

```json
{
  "items": [
    {
      "key": "INC-4822",
      "title": "Login fails for some customers",
      "service": "login-service",
      "priority": "P1",
      "status": "open",
      "opened_at": "2026-10-13T19:01:00Z"
    },
    {
      "key": "INC-4821",
      "title": "Login fails for some customers",
      "service": "login-service",
      "priority": "P1",
      "status": "acknowledged",
      "opened_at": "2026-10-13T19:00:00Z"
    }
  ],
  "next_page": null
}
```

**Errors:** `422` if `page` is less than `1` or is not a valid integer.

## `GET /mobile/v1/incidents/{key}`

Returns the incident identified by `key`.

**Request:** `key` is a path parameter.

**Success (`200`):** An object with `key`, `title`, `service`, `priority`,
`status`, `opened_at`, and `timeline`. Timeline events are ordered oldest
first; each event has `at`, `kind`, and `note`.

```json
{
  "key": "INC-4821",
  "title": "Login fails for some customers",
  "service": "login-service",
  "priority": "P1",
  "status": "acknowledged",
  "opened_at": "2026-10-13T19:00:00Z",
  "timeline": [
    {
      "at": "2026-10-13T19:00:00Z",
      "kind": "opened",
      "note": ""
    },
    {
      "at": "2026-10-13T19:05:00Z",
      "kind": "acknowledged",
      "note": "On it"
    }
  ]
}
```

**Errors:** `404` when the key is unknown:

```json
{"error": "not_found"}
```

## `POST /mobile/v1/subscriptions`

Creates a subscription.

**Request:** JSON body with `engineer` (string), `services` (array of service
slugs), and `min_priority` (one of `P1`, `P2`, `P3`, or `P4`).

```json
{
  "engineer": "a.reyes",
  "services": ["login-service"],
  "min_priority": "P2"
}
```

**Success (`201`):** The created subscription object:

```json
{
  "id": 1,
  "engineer": "a.reyes",
  "services": ["login-service"],
  "min_priority": "P2"
}
```

**Errors:** `422` for missing or invalid body fields. An unknown service also
returns `422`, with a `detail` message identifying the unknown service(s).

## `GET /mobile/v1/subscriptions`

Lists subscriptions for an engineer, ordered by subscription ID.

**Request:** Required query parameter `engineer` (string).

**Success (`200`):** An array of subscription objects, each containing `id`,
`engineer`, `services`, and `min_priority`. No matches returns an empty array.

```json
[
  {
    "id": 1,
    "engineer": "a.reyes",
    "services": ["login-service"],
    "min_priority": "P2"
  }
]
```

**Errors:** `422` if the required `engineer` query parameter is missing.
