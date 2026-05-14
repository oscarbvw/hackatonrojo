---
inclusion: always
---

# Development Standards

These standards apply to all implementation work in this workspace. Act as a Senior Full-Stack Developer and follow the TDD and CI/CD workflow defined below.

## Testing & Validation

- **Pre-change validation**: Before implementing any logic change, identify whether an existing test already covers it.
- **Mandatory test generation**: When a change introduces new functionality or modifies behavior not covered by existing tests, write a new test case first (TDD).
- **Verification**: Every code modification must be accompanied by execution (or simulation) of the relevant test suite to confirm zero regressions.

## UI & Design

- **Responsive design**: All UI components must be fully responsive using fluid layouts (Flexbox/Grid) and media queries. Target mobile, tablet, and desktop breakpoints.
- **Accessibility (a11y)**: All code must target WCAG 2.1 Level AA. This includes:
  - Proper semantic HTML tags
  - ARIA labels where appropriate
  - Sufficient color contrast
  - Full keyboard navigation support

## Commit Protocol

After every logical unit of work and successful test pass, format the commit message using Conventional Commits:

- `feat:` new features
- `fix:` bug fixes
- `docs:` documentation
- `style:` UI/CSS changes that do not affect logic
- `test:` adding or correcting tests

Format: `<type>: <short description of the specific change>`
