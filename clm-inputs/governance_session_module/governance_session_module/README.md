# Governance Session Module v3

This version introduces context-specific adapters while keeping the core engine generic.

## Core engine
- Governance Session
- Session Participant
- Session Agenda Item
- Session Resolution
- Session Action
- Session Evidence
- Session Signature

## Core features
- participants
- quorum validation
- minutes lock validation
- signatures
- resolution gating

## Adapter architecture
- adapters/procurement/
  - procurement session templates
  - procurement adapter logic
  - procurement integration notes

## Why this matters
The core module stays reusable across Procurement, HR, Audit, Board, and other contexts.
Domain-specific behavior now belongs in adapters instead of being hardcoded into the engine.
