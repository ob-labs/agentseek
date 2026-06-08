import type { ReactNode } from "react";

type ConnectionBannerProps = {
  connected: boolean;
  sessionUrl: string | null;
  onDisconnect: () => void;
  onRejoin: () => void;
  isLoading: boolean;
};

export default function ConnectionBanner({
  connected,
  sessionUrl,
  onDisconnect,
  onRejoin,
  isLoading,
}: ConnectionBannerProps): ReactNode {
  return (
    <section className="thread-banner" aria-label="Session link">
      <div className="thread-banner__copy">
        <strong>
          {!connected
            ? "Disconnected"
            : sessionUrl
              ? "Session link active"
              : "Session link ready"}
        </strong>
        <span>
          {!connected
            ? "The agent may still be running in the sandbox. Click Rejoin to reconnect."
            : sessionUrl
              ? "Reopen this conversation later with the current URL."
              : "After the first message, this page adds a thread URL so you can reopen the same conversation later."}
        </span>
      </div>
      <div className="thread-banner__actions">
        {connected && isLoading && (
          <button
            type="button"
            className="thread-banner__btn thread-banner__btn--disconnect"
            onClick={onDisconnect}
          >
            Disconnect
          </button>
        )}
        {!connected && (
          <button
            type="button"
            className="thread-banner__btn thread-banner__btn--rejoin"
            onClick={onRejoin}
          >
            Rejoin
          </button>
        )}
      </div>
      {sessionUrl ? (
        <code className="thread-banner__url">{sessionUrl}</code>
      ) : null}
    </section>
  );
}
