import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Anotação cega | DODF 112",
  description:
    "Ambiente independente para calibrar a anotação humana das páginas 37 e 51 do DODF 112.",
};

export default function AnnotationLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return children;
}
