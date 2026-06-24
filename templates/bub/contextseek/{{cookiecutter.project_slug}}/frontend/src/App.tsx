import { CopilotChat, CopilotKit } from "@copilotkit/react-core/v2";
import "@copilotkit/react-core/v2/styles.css";

const RUNTIME_URL = import.meta.env.VITE_COPILOTKIT_RUNTIME_URL || "/api/copilotkit";

export function App() {
  return (
    <CopilotKit runtimeUrl={RUNTIME_URL} useSingleEndpoint={false}>
      <div className="app-root">
        <CopilotChat agentId="default" />
      </div>
    </CopilotKit>
  );
}
