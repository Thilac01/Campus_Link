# Testing

Install development dependencies and run `pytest`. Current automated tests cover settings recovery,
profile persistence, schema creation, fragmented/coalesced frames, oversized frames, and transfer
path traversal.

## Milestone test plan

- Phase 2: identity lifecycle, trust/key changes, TLS authentication, discovery, rate limits.
- Phase 3: ordering, deduplication, acknowledgements, offline queue, reconnect, two instances.
- Phase 4: hashes, resume ranges, source changes, cancellation, traversal/symlinks, low disk,
  receiver restarts, bounded memory, generated 1 KB through 10 GB datasets.
- Phases 6–8: consent/revocation, capture indicator, emergency stop, media device loss and jitter.
- Phase 10: update signature failures, rollback, clean install/upgrade/uninstall.

Network impairment will use a test harness with configurable latency, loss, interruption, and
bandwidth. Performance results must record hardware, versions, dataset generation, and method;
no target result is assumed in advance.

