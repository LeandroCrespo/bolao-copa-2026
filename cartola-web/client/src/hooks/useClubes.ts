import { trpc } from "@/lib/trpc";
import { useMemo } from "react";

export interface ClubeInfo {
  id: number;
  nome: string;
  abreviacao: string;
  escudo30: string;
  escudo45: string;
  escudo60: string;
}

/**
 * Hook to get clubes data from Cartola API with caching.
 * Returns a map of clube_id -> ClubeInfo and helpers.
 */
export function useClubes() {
  const { data: rawClubes } = trpc.cartola.clubes.useQuery(undefined, {
    staleTime: 1000 * 60 * 60,
    gcTime: 1000 * 60 * 60 * 2,
  });

  const clubes = useMemo(() => {
    if (!rawClubes) return new Map<number, ClubeInfo>();
    const map = new Map<number, ClubeInfo>();
    for (const [id, info] of Object.entries(rawClubes)) {
      const clube = info as { id?: number; nome?: string; abreviacao?: string; escudos?: Record<string, string> };
      map.set(Number(id), {
        id: Number(id),
        nome: clube.nome || "",
        abreviacao: clube.abreviacao || "",
        escudo30: clube.escudos?.["30x30"] || "",
        escudo45: clube.escudos?.["45x45"] || "",
        escudo60: clube.escudos?.["60x60"] || "",
      });
    }
    return map;
  }, [rawClubes]);

  const getEscudo = (clubeId: number | string | undefined, size: "30" | "45" | "60" = "30") => {
    if (!clubeId) return "";
    const clube = clubes.get(Number(clubeId));
    if (!clube) return "";
    if (size === "60") return clube.escudo60;
    if (size === "45") return clube.escudo45;
    return clube.escudo30;
  };

  const getNome = (clubeId: number | string | undefined) => {
    if (!clubeId) return "";
    return clubes.get(Number(clubeId))?.nome || "";
  };

  const getAbreviacao = (clubeId: number | string | undefined) => {
    if (!clubeId) return "";
    return clubes.get(Number(clubeId))?.abreviacao || "";
  };

  return { clubes, getEscudo, getNome, getAbreviacao };
}
