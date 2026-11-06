# Mobile API

All endpoints are under `/mobile/v1`. Timestamps are returned in UTC with a
`Z` suffix.

## `GET /mobile/v1/incidents` — incident list

### Request

No request body. Optional query parameter:

| Parameter | Type | Default | Constraint | Meaning |
| --- | --- | --- | --- | --- |
| `page` | integer | `1` | At least `1` | One-based page number. |

### Success response

`200 OK`. The response has `items` and `next_page`. Each item has `key`,
`title`, `service` (service slug), `priority`, `status`, and `opened_at`
(timestamp). The list excludes resolved incidents, orders by newest `opened_at`
first (then newest incident ID first for equal timestamps), and contains at
most 20 items. `next_page` is the next page number when another page exists;
otherwise it is `null`.

Issue #41's response example shows a page with another page available:

```json
{
  "items": [
    {
      "key": "INC-4821",
      "title": "Login fails for some customers",
      "service": "login-service",
      "priority": "P1",
      "status": "acknowledged",
      "opened_at": "2026-10-13T19:00:00Z"
    }
  ],
  "next_page": 2
}
```

The following response is asserted by
`test_mobile_incidents_include_fields_and_exclude_resolved`:

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

In particular, this test verifies that `acknowledged` incidents are included
and resolved incidents are excluded.

### Pagination example

`test_mobile_incidents_are_paginated_in_pages_of_20` creates 21 incidents. A
request to `GET /mobile/v1/incidents` returns 20 items, starts with
`INC-21`, and has `"next_page": 2`. The test then requests
`GET /mobile/v1/incidents?page=2`; its exact response is:

```json
{
  "items": [
    {
      "key": "INC-1",
      "title": "Login fails for some customers",
      "service": "login-service",
      "priority": "P1",
      "status": "open",
      "opened_at": "2026-10-13T19:00:00Z"
    }
  ],
  "next_page": null
}
```

### Errors

A `page` value below `1` violates the query constraint in the implementation
and is rejected with `422 Unprocessable Entity`. The mobile API test does not
assert the validation-error body, so no error JSON example is specified here.

## `GET /mobile/v1/incidents/{key}` — incident detail and timeline

### Request

The incident key is supplied as the `{key}` path parameter. For example:
`GET /mobile/v1/incidents/INC-4821`. The issue does not specify a request body
or query parameters.

### Success response

Issue #42's example contains an `opened` event. The endpoint test
`test_incident_detail_with_timeline_oldest_first` also verifies that a later
acknowledgment is returned after it:

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

### Errors

For an unknown key, issue #42 specifies `404 Not Found` with this body:

```json
{"error": "not_found"}
```

`test_unknown_key_is_not_found` asserts this status and response.

## `POST /mobile/v1/subscriptions` — create an alert subscription

### Request

Send a JSON body with the engineer name, service slugs, and minimum priority.
`min_priority` must be one of `P1`, `P2`, `P3`, or `P4`. Issue #43 gives this
request:

```json
{
  "engineer": "a.reyes",
  "services": ["login-service"],
  "min_priority": "P2"
}
```

### Success response

`201 Created`. The response contains the saved subscription. Its `id` is an
integer:

`test_create_subscription_returns_stored_fields_and_id` asserts this response:

```json
{
  "id": 1,
  "engineer": "a.reyes",
  "services": ["login-service"],
  "min_priority": "P2"
}
```

### Errors

An unknown service returns `422 Unprocessable Entity` and does not create a
subscription. For example:

```json
{"detail": "Unknown service(s): missing-service"}
```

`test_unknown_service_is_rejected_without_saving_subscription` asserts the
status and that no subscription is stored.

Invalid or missing request fields, including a `min_priority` outside `P1`–`P4`,
also return `422 Unprocessable Entity` with FastAPI's validation error body.

## `GET /mobile/v1/subscriptions` — list alert subscriptions

### Request

The engineer is specified by the `engineer` query parameter. Issue #43 gives
this request:

```http
GET /mobile/v1/subscriptions?engineer=a.reyes
```

### Success response

`200 OK`. The response is an array containing only subscriptions for the
requested engineer, ordered by ID. No matching subscriptions returns an empty
array. For example:

`test_list_subscriptions_is_scoped_to_engineer` verifies engineer-scoped
results:

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

### Errors

The required `engineer` query parameter must be provided. If it is missing, the
endpoint returns `422 Unprocessable Entity` with FastAPI's validation error
body.
