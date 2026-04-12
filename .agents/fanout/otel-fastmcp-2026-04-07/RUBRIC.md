# Fan-In Rubric

Use this rubric when comparing telemetry workstreams and deciding what to keep.

## 1. Semconv Alignment

- Does the change move FastMCP materially closer to the MCP semantic conventions?
- Are new attributes and names standard where possible?
- Are custom `fastmcp.*` attributes still justified and well-scoped?

## 2. Agent Trace Quality

- Would the resulting traces look better inside Logfire or Elastic?
- Does the design compose well with outer agent traces?
- Does it help answer the questions practitioners actually ask?

## 3. Protocol Coverage

- Does the implementation improve coverage of important MCP lifecycle operations?
- Is the seam coherent, or is it a patchwork of wrappers?

## 4. Verification Quality

- Are there deterministic tests for span names, attributes, parentage, and errors?
- Is any end-to-end OTLP smoke path worth its maintenance cost?

## 5. Codebase Fit

- Does the implementation feel like FastMCP?
- Is the code readable and likely to be maintainable?
- Does it fix causes instead of compensating around them?

## 6. Cardinality And Cost

- Does the design avoid obvious high-cardinality traps?
- Does it add useful signal without producing noisy traces?

## 7. Metrics Value

- If metrics were added, are they the right ones?
- If metrics were not added, is the reason persuasive?

## 8. Docs And Demos

- Would a FastMCP user understand how to enable and inspect the new telemetry?
- Are Logfire and Elastic shown concretely enough to feel first-class?

## 9. Mergeability

- Could we merge the patch directly, cherry-pick parts, or treat it as a design prototype?
- Is the resulting sequencing plan clear?

## Preferred Outcome

The best result is not necessarily the biggest diff.
Prefer the implementation that most improves:

1. trace usefulness
2. framework coherence
3. confidence in correctness

If two diffs are complementary, plan an integration path instead of choosing only one.
