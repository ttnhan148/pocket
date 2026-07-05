import TemplateEditorPageClient from "./template-editor-client";

export function generateStaticParams() {
  return [{ id: "1" }];
}

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  return <TemplateEditorPageClient params={params} />;
}
