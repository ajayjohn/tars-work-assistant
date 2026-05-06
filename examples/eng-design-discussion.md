# Engineering example: design discussion

Thread: Search indexing design review

Alex: We need to decide whether indexing happens synchronously on note write or asynchronously during maintenance.
Sam: Synchronous indexing gives users immediate search results, but it makes every write slower and more failure-prone.
Priya: The current write path already validates frontmatter and wikilinks. Adding embedding generation there feels risky.
Lee: Agree. Keyword indexing could be synchronous, but semantic embeddings should be async.
Alex: Decision proposal: write note first, update FTS immediately when cheap, queue semantic indexing for maintenance.
Sam: I support that if failed semantic indexing does not block the user.
Priya: Open question one: where does the queue live? `_system/index-queue.yaml` or telemetry?
Lee: Queue should be explicit, not hidden in telemetry. Telemetry is for observation, not work state.
Alex: Open question two: how do we prevent stale search results after a note is moved?
Sam: Move operation should enqueue both old path deletion and new path indexing.
Priya: Risk: queue corruption could make search silently incomplete.
Lee: We can add a weekly reconciliation that scans modified files and compares against the index.
Alex: Decision: direct note writes stay the source of truth. Search is derived and can be rebuilt.
Sam: Task for me: add a reconciliation check to the maintenance script by Friday.
Priya: I'll update the MCP schema docs so tools describe async semantic indexing clearly.
Lee: One more concern: if the first semantic search downloads the model, users may think the app froze.
Alex: Good catch. We need a one-time warning before first semantic search.
Sam: Should we expose a command to rebuild search manually?
Priya: Maybe later. For now `/maintain` can handle it.
Alex: Final decision: sync FTS where cheap, async semantic indexing, explicit queue, weekly reconciliation.
