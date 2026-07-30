import { describe, it, expect, beforeEach } from "vitest";
import { VoiceStateMachine } from "../../src/services/voice/voiceStateMachine";

describe("VoiceStateMachine", () => {
  let machine;

  beforeEach(() => {
    machine = new VoiceStateMachine();
  });

  it("starts in IDLE state", () => {
    expect(machine.state).toBe("IDLE");
  });

  it("transitions IDLE → REQUEST_PERMISSION", () => {
    const ok = machine.transition("REQUEST_PERMISSION");
    expect(ok).toBe(true);
    expect(machine.state).toBe("REQUEST_PERMISSION");
  });

  it("transitions through the happy path", () => {
    machine.transition("REQUEST_PERMISSION");
    machine.transition("READY");
    machine.transition("LISTENING");
    machine.transition("RECORDING");
    machine.transition("UPLOADING");
    machine.transition("TRANSCRIBING");
    machine.transition("THINKING");
    machine.transition("STREAMING_RESPONSE");
    machine.transition("COMPLETE");
    expect(machine.state).toBe("COMPLETE");
  });

  it("rejects invalid transitions and stays in current state", () => {
    expect(machine.state).toBe("IDLE");
    const ok = machine.transition("TRANSCRIBING"); // IDLE → TRANSCRIBING is invalid
    expect(ok).toBe(false);
    expect(machine.state).toBe("IDLE"); // unchanged
  });

  it("no-ops when transitioning to the same state", () => {
    machine.transition("REQUEST_PERMISSION");
    const ok = machine.transition("REQUEST_PERMISSION");
    expect(ok).toBe(true); // no-op returns true
    expect(machine.state).toBe("REQUEST_PERMISSION");
  });

  it("resets to IDLE from any state", () => {
    machine.transition("REQUEST_PERMISSION");
    machine.transition("READY");
    machine.transition("LISTENING");
    machine.reset();
    expect(machine.state).toBe("IDLE");
  });

  it("isActive is false in IDLE", () => {
    expect(machine.isActive).toBe(false);
  });

  it("isActive is true when not IDLE", () => {
    machine.transition("REQUEST_PERMISSION");
    expect(machine.isActive).toBe(true);
  });

  it("isProcessing is true during UPLOADING → STREAMING_RESPONSE", () => {
    machine.transition("REQUEST_PERMISSION");
    machine.transition("READY");
    machine.transition("LISTENING");
    machine.transition("UPLOADING");
    expect(machine.isProcessing).toBe(true);

    machine.transition("TRANSCRIBING");
    expect(machine.isProcessing).toBe(true);

    machine.transition("THINKING");
    expect(machine.isProcessing).toBe(true);
  });

  it("fires onChange callback on valid transition", () => {
    const changes = [];
    const m = new VoiceStateMachine((newState, prevState) => {
      changes.push({ newState, prevState });
    });

    m.transition("REQUEST_PERMISSION");
    m.transition("READY");

    expect(changes).toEqual([
      { newState: "REQUEST_PERMISSION", prevState: "IDLE" },
      { newState: "READY", prevState: "REQUEST_PERMISSION" },
    ]);
  });

  it("can recover from ERROR state to LISTENING", () => {
    machine.transition("REQUEST_PERMISSION");
    machine.transition("ERROR");
    expect(machine.state).toBe("ERROR");

    const ok = machine.transition("LISTENING");
    expect(ok).toBe(true);
    expect(machine.state).toBe("LISTENING");
  });
});
