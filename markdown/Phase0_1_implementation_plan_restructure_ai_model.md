# Restructure AI Model Creation Pages (Revised Flow)

Refine the AI Model creation and edit steps to use a dynamic layout based on the provider selection.

## User Review Required

> [!IMPORTANT]
> - **Flow for Standard Providers**: Step 1 will only show:
>   1. **Provider Type** *
>   2. **Provider Name** *
>   3. **Model Type** *
>   4. **Model Selection** * (A select dropdown populated dynamically based on the selected Provider and Model Type. If no predefined models match, a text input is shown to let the user enter a custom model name).
>   *Note: Model Name and Model Code will be auto-generated in the background based on the model selected to keep the UI clean.*
>
> - **Flow for Internal Custom Models**: If the user selects **Internal Custom** for Provider Type and **Custom** for Provider Name, the UI on Step 1 will dynamically expand to display the following list of fields:
>   - **Model Code** *
>   - **Model Name** *
>   - **Version**
>   - **Model Owner Department**
>   - **Model Developed By**
>   - **Training Data Source**
>   - **Fine-tuned From**
>   - **Hosting Environment**
>   - **Security Classification**
>   - **Approved Usage**
>   - **Restricted Usage**
>   - **Model Card Available?** (Yes/No)
>   - **Evaluation Completed?** (Yes/No)
>   - **Responsible Person**

---

## Open Questions

> [!NOTE]
> - **Provider Name "Custom" Option**: We will add the option **Custom** to the Provider Name dropdown so the user can explicitly trigger this layout.

---

## Proposed Changes

### Frontend Components

***

#### [MODIFY] [ModelFormModal.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/registry/ModelFormModal.tsx)

- Update `PROVIDER_NAMES` list to include `"Custom"`.
- Define a dictionary mapping `PROVIDER_MODELS` by Provider Name and Model Type:
  - OpenAI Enterprise: LLM -> `[gpt-4o, gpt-4-turbo, gpt-4, gpt-3.5-turbo]`, EMBEDDING -> `[text-embedding-3-small, text-embedding-3-large]`
  - Anthropic: LLM -> `[claude-3-5-sonnet, claude-3-opus, claude-3-haiku]`
  - AWS Bedrock: LLM -> `[meta.llama3-70b-instruct, anthropic.claude-3-sonnet, cohere.command-r-v1]`
  - Azure OpenAI: LLM -> `[gpt-4o, gpt-4-turbo, gpt-3.5-turbo]`
  - Google Vertex AI: LLM -> `[gemini-1.5-pro, gemini-1.5-flash, gemini-1.0-pro]`, EMBEDDING -> `[text-embedding-gecko]`
  - Hugging Face Hub: LLM -> `[meta-llama/Meta-Llama-3-8B-Instruct, mistralai/Mistral-7B-Instruct-v0.3]`, CLASSIFIER -> `[distilbert-base-uncased-finetuned-sst-2-english]`
  - Meta: LLM -> `[llama-3-8b, llama-3-70b]`
  - Mistral: LLM -> `[mistral-large, mistral-medium, open-mixtral-8x22b]`
  - Cohere: LLM -> `[command-r-plus, command-r]`, EMBEDDING -> `[embed-english-v3.0]`
  - Internal Innovant: LLM -> `[innovant-core-llm, innovant-chat-v2]`, CLASSIFIER -> `[innovant-risk-classifier-v1]`
  - Client Internal Model: LLM -> `[client-internal-llm-v1]`
- Update `loadModel` to support editing:
  - If the loaded model provider type is `"Internal Custom"` and provider name is `"Custom"`, set `formData.provider_name = "Custom"`.
  - Otherwise, match it to the standard list or custom dropdown mappings.
- Update `validateAndAdvance` for Step 1 validation:
  - If `"Internal Custom"` + `"Custom"`, validate that `model_code` and `model_name` are not empty.
  - If standard provider, validate that `provider_type`, `provider_name`, `model_type`, and the selected model are not empty.
- Update `handleSubmit`:
  - If a standard provider was chosen, ensure `model_name` is set to the selected model value, and `model_code` is set to the sanitized uppercase version of the selected model name (ensuring uniqueness by appending a brief suffix if creating).
- Restructure the JSX layout in Step 1 (Core parameters):
  - Always render **Provider Type**, **Provider Name**, and **Model Type** select fields first.
  - If `provider_type === "Internal Custom" && provider_name === "Custom"`:
    - Render Model Code, Model Name, Version, followed by the 11 model source details fields in grid format.
  - Otherwise:
    - Retrieve the list of models matching `PROVIDER_MODELS[provider_name]?.[model_type]`.
    - If models exist, render a **Model** dropdown select field.
    - If no predefined models exist, render a **Model Name** text input field.
    - Automatically update both `model_name` and `model_code` state values on selection/change of this model field.

---

## Verification Plan

### Automated Tests
- Build verification via `npm run build` or `npx tsc --noEmit`.

### Manual Verification
1. Open the model creation modal.
2. Select **Provider Type** = "Enterprise Vendor", **Provider Name** = "OpenAI Enterprise", and **Model Type** = "LLM".
   - Verify that the **Model** dropdown displays `gpt-4o`, `gpt-4-turbo`, etc.
   - Verify that no other fields (Model Code, Model Name, Version, Source Details) are visible.
3. Select **Provider Type** = "Internal Custom" and **Provider Name** = "Custom".
   - Verify that all custom model fields appear (Model Code, Model Name, Version, Owner Dept, Developed By, etc.).
4. Test modal validation by leaving required fields blank and verify that error toasts are shown.
5. Create a model of each type and verify that they are successfully registered in the database.
