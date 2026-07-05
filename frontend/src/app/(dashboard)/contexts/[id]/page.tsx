import ContextEditorPageClient from "./context-editor-client";

export function generateStaticParams() {
  return [{ id: "1" }];
}

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  return <ContextEditorPageClient params={params} />;
}
