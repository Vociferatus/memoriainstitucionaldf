import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Revisão assistida | DODF 112",
  description: "Fila de decisões por risco para validar resultados automáticos do DODF 112.",
};

export default function ReviewLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return children;
}
