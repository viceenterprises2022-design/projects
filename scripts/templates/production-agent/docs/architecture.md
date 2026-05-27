# Architecture Reference

This document highlights the design and security implementation details.

## State Loop
The core transitions run within a structured Plan-Act-Observe stategraph:
1. **Plan**: Analyze context, build steps, query classifiers.
2. **Act**: Invoke selected tools and collect outputs.
3. **Observe**: Run outputs against security audits before responding to the user.

## Adrian Runtime Defense Harness
Our middleware captures action traces, sanitizes credit card and phone digits, evaluates intent rules against the contract, and gates tool parameters.
