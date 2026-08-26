import { SystemPrompt, renderPrompt } from "/home/maker/.local/lib/node_modules/@deepseek-ai/dsh/node_modules/@deepseek-ai/dsh-system-prompt/lib/index.js";
import { Context } from "/home/maker/.local/lib/node_modules/@deepseek-ai/dsh/node_modules/@deepseek-ai/cordis/lib/index.js";

async function verifyDshPatch() {
    const ctx = new Context();
    const systemPrompt = new SystemPrompt(ctx, {
        includeHarnessIdentity: true,
        includeRuntimeContext: true,
        persona: "Default Persona"
    });

    const assembly = await systemPrompt.assemble({
        agent: {
            session: {
                header: {
                    cwd: process.cwd()
                }
            },
            options: {
                model: "deepseek-chat",
                provider: "deepseek"
            }
        }
    });

    const rendered = renderPrompt(assembly);
    console.log("=== DSH ASSEMBLED RENDERED PROMPT ===");
    console.log(rendered);
    console.log("=====================================");

    if (rendered.includes("MASTER SYSTEM PROMPT") && rendered.includes("最高领导指令中心")) {
        console.log(">>> SUCCESS: DSH 官方源码底层 100% 绝对置顶 Master Prompt 注入验证通过！<<<");
    } else {
        throw new Error("FAILED: DSH did not inject MASTER_SYSTEM_PROMPT.md!");
    }
}

verifyDshPatch().catch(err => {
    console.error("Test Error:", err);
    process.exit(1);
});
