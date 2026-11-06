# Mobile API

## `GET /mobile/v1/incidents`

Returns a page of incidents that are not resolved, ordered by most recently
opened first (with incident ID as a tie-breaker). Pages contain up to 20 items.

### Request

- Query parameter `page` (integer, optional): page number, starting at `1`.
  Defaults to `1`; values below `1` are rejected with HTTP `422`.
- No request body.

### Response

HTTP `200`. The response contains:

- `items`: an array of incidents. Each item has `key`, `title`, `service`
  (service slug), `priority`, `status`, and `opened_at` (date-time).
- `next_page`: the next page number when another page is available, otherwise
  `null`.

Example response:

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

Proven by: tests/api/test_mobile_incident_list.py::test_mobile_incidents_include_fields_and_exclude_resolved

When more results are available, `next_page` is the following page number;
the pagination test confirms a first-page value of `2` for 21 incidents and
that page 2 contains the remaining incident.

### Errors

- HTTP `422` for an invalid `page` value, including values below `1`.
- The endpoint defines no other application-specific error responses.
