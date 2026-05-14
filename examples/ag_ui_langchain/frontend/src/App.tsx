import { CopilotChat, CopilotKit } from "@copilotkit/react-core/v2";
import "@copilotkit/react-core/v2/styles.css";

import { HashbrownAssistantMarkdown, LangChainGenerativeUiProvider } from "./langchainCopilotKitUi";

const RUNTIME_URL = import.meta.env.VITE_COPILOTKIT_RUNTIME_URL || "/api/copilotkit";

export function App() {
  return (
    <CopilotKit runtimeUrl={RUNTIME_URL} useSingleEndpoint={false}>
      <LangChainGenerativeUiProvider>
        <div className="app-root">
          <CopilotChat
            agentId="default"
            messageView={{
              assistantMessage: {
                markdownRenderer: HashbrownAssistantMarkdown,
              },
            }}
          />
        </div>
      </LangChainGenerativeUiProvider>
    </CopilotKit>
  );
}
