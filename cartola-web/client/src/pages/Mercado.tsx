import { trpc } from "@/lib/trpc";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2 } from "lucide-react";
import { useMemo, useState } from "react";
import { useLocation } from "wouter";
import { ClubeBadge } from "@/components/ClubeBadge";

const POSICOES: Record<number, string> = { 1: "GOL", 2: "LAT", 3: "ZAG", 4: "MEI", 5: "ATA", 6: "TEC" };
const POS_ORDER = [1, 3, 2, 4, 5, 6];
const POS_COLORS: Record<string, { bg: string; text: string }> = {
  GOL: { bg: "rgba(234, 179, 8, 0.15)", text: "#EAB308" },
  LAT: { bg: "rgba(34, 197, 94, 0.15)", text: "#22C55E" },
  ZAG: { bg: "rgba(59, 130, 246, 0.15)", text: "#3B82F6" },
  MEI: { bg: "rgba(168, 85, 247, 0.15)", text: "#A855F7" },
  ATA: { bg: "rgba(239, 68, 68, 0.15)", text: "#EF4444" },
  TEC: { bg: "rgba(107, 114, 128, 0.15)", text: "#6B7280" },
};
const STATUS_JOGADOR: Record<number, { label: string; color: string }> = {
  2: { label: "Dúvida", color: "#EAB308" },
  3: { label: "Suspenso", color: "#EF4444" },
  5: { label: "Contundido", color: "#EF4444" },
  6: { label: "Nulo", color: "#6B7280" },
  7: { label: "Provável", color: "#22C55E" },
};

type SortField = "score" | "preco" | "media" | "variacao_num" | "custo_beneficio";

export default function Mercado() {
  const [, setLocation] = useLocation();
  const [busca, setBusca] = useState("");
  const [posicaoFiltro, setPosicaoFiltro] = useState("todas");
  const [statusFiltro, setStatusFiltro] = useState("todos");
  const [sortField, setSortField] = useState<SortField>("score");
  const [sortAsc, setSortAsc] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"posicao" | "tabela">("posicao");

  const { data: mercado } = trpc.cartola.mercadoStatus.useQuery();
  const { data, isLoading } = trpc.estrategia.mercadoComScores.useQuery();

  const atletasFiltrados = useMemo(() => {
    if (!data?.atletas) return [];
    let list = [...data.atletas];
    if (busca) {
      const term = busca.toLowerCase();
      list = list.filter((a: any) => a.apelido?.toLowerCase().includes(term) || a.clube_nome?.toLowerCase().includes(term));
    }
    if (posicaoFiltro !== "todas") list = list.filter((a: any) => a.posicao_id === Number(posicaoFiltro));
    if (statusFiltro !== "todos") list = list.filter((a: any) => a.status_id === Number(statusFiltro));
    list.sort((a: any, b: any) => {
      const va = a[sortField] ?? 0;
      const vb = b[sortField] ?? 0;
      return sortAsc ? va - vb : vb - va;
    });
    return list;
  }, [data, busca, posicaoFiltro, statusFiltro, sortField, sortAsc]);

  // Group by position
  const porPosicao = useMemo(() => {
    const map: Record<number, any[]> = {};
    for (const a of atletasFiltrados) {
      const pid = a.posicao_id;
      if (!map[pid]) map[pid] = [];
      map[pid].push(a);
    }
    return map;
  }, [atletasFiltrados]);

  const provaveis = atletasFiltrados.filter((a: any) => a.status_id === 7).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold" style={{ color: "#f1f5f9", fontFamily: "var(--font-heading)" }}>
          📊 Mercado Completo
        </h1>
        <p className="text-sm mt-1" style={{ color: "#94a3b8" }}>
          Todos os jogadores disponíveis, ranqueados por posição (do melhor para o pior)
        </p>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-3 gap-4">
        <div className="rounded-xl p-4 text-center" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
          <p className="text-xs" style={{ color: "#94a3b8" }}>🎯 Rodada</p>
          <p className="text-2xl font-bold" style={{ color: "#54b4f7" }}>{mercado?.rodada_atual || "—"}</p>
        </div>
        <div className="rounded-xl p-4 text-center" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
          <p className="text-xs" style={{ color: "#94a3b8" }}>⚽ Jogadores</p>
          <p className="text-2xl font-bold" style={{ color: "#f1f5f9" }}>{atletasFiltrados.length}</p>
        </div>
        <div className="rounded-xl p-4 text-center" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
          <p className="text-xs" style={{ color: "#94a3b8" }}>✅ Prováveis</p>
          <p className="text-2xl font-bold" style={{ color: "#22C55E" }}>{provaveis}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="rounded-xl p-4" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
          <div className="lg:col-span-2 relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: "#64748b" }}>🔍</span>
            <Input placeholder="Buscar jogador ou clube..." value={busca}
              onChange={(e) => setBusca(e.target.value)} className="pl-10"
              style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(148, 163, 184, 0.2)", color: "#f1f5f9" }} />
          </div>
          <Select value={posicaoFiltro} onValueChange={setPosicaoFiltro}>
            <SelectTrigger style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(148, 163, 184, 0.2)", color: "#f1f5f9" }}>
              <SelectValue placeholder="Posição" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="todas">Todas Posições</SelectItem>
              {Object.entries(POSICOES).map(([id, nome]) => <SelectItem key={id} value={id}>{nome}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={statusFiltro} onValueChange={setStatusFiltro}>
            <SelectTrigger style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(148, 163, 184, 0.2)", color: "#f1f5f9" }}>
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="todos">Todos Status</SelectItem>
              {Object.entries(STATUS_JOGADOR).map(([id, { label }]) => <SelectItem key={id} value={id}>{label}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={sortField} onValueChange={(v) => setSortField(v as SortField)}>
            <SelectTrigger style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(148, 163, 184, 0.2)", color: "#f1f5f9" }}>
              <SelectValue placeholder="Ordenar" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="score">Score V7</SelectItem>
              <SelectItem value="preco">Preço</SelectItem>
              <SelectItem value="media">Média</SelectItem>
              <SelectItem value="variacao_num">Variação</SelectItem>
              <SelectItem value="custo_beneficio">Custo/Benefício</SelectItem>
            </SelectContent>
          </Select>
          <div className="flex gap-2">
            <Button variant={viewMode === "posicao" ? "default" : "outline"} size="sm" className="flex-1"
              onClick={() => setViewMode("posicao")} style={viewMode === "posicao" ? { background: "#54b4f7", color: "#000" } : {}}>
              Por Posição
            </Button>
            <Button variant={viewMode === "tabela" ? "default" : "outline"} size="sm" className="flex-1"
              onClick={() => setViewMode("tabela")} style={viewMode === "tabela" ? { background: "#54b4f7", color: "#000" } : {}}>
              Tabela
            </Button>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center min-h-[40vh]">
          <Loader2 className="h-8 w-8 animate-spin" style={{ color: "#54b4f7" }} />
        </div>
      ) : atletasFiltrados.length === 0 ? (
        <div className="rounded-xl p-8 text-center" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
          <p style={{ color: "#94a3b8" }}>Nenhum atleta encontrado.</p>
        </div>
      ) : viewMode === "posicao" ? (
        /* View by Position - Streamlit style */
        <div className="space-y-6">
          {POS_ORDER.map((posId) => {
            const jogadores = porPosicao[posId];
            if (!jogadores || jogadores.length === 0) return null;
            const posNome = POSICOES[posId];
            const colors = POS_COLORS[posNome];
            return (
              <div key={posId}>
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-lg font-bold px-4 py-1 rounded-lg" style={{ background: colors.bg, color: colors.text }}>
                    {posNome}
                  </span>
                  <span className="text-sm" style={{ color: "#64748b" }}>{jogadores.length} jogadores</span>
                </div>
                <div className="space-y-2">
                  {jogadores.slice(0, 20).map((a: any, i: number) => (
                    <PlayerCard key={a.atleta_id} atleta={a} ranking={i + 1} posNome={posNome}
                      expanded={expandedId === a.atleta_id}
                      onToggle={() => setExpandedId(expandedId === a.atleta_id ? null : a.atleta_id)}
                      onAnalise={() => setLocation(`/jogador/${a.atleta_id}`)} />
                  ))}
                  {jogadores.length > 20 && (
                    <p className="text-xs text-center py-2" style={{ color: "#64748b" }}>
                      + {jogadores.length - 20} jogadores não exibidos. Use a busca para encontrar.
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* Table view */
        <div className="rounded-xl overflow-hidden" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: "1px solid rgba(148, 163, 184, 0.15)" }}>
                  <th className="text-left py-3 px-3" style={{ color: "#94a3b8" }}>#</th>
                  <th className="text-left py-3 px-3" style={{ color: "#94a3b8" }}>Jogador</th>
                  <th className="text-center py-3 px-2" style={{ color: "#94a3b8" }}>Pos</th>
                  <th className="text-left py-3 px-2" style={{ color: "#94a3b8" }}>Clube</th>
                  <th className="text-center py-3 px-2" style={{ color: "#94a3b8" }}>Status</th>
                  <th className="text-right py-3 px-2 cursor-pointer" style={{ color: sortField === "score" ? "#54b4f7" : "#94a3b8" }} onClick={() => { setSortField("score"); setSortAsc(!sortAsc); }}>Score</th>
                  <th className="text-right py-3 px-2 cursor-pointer" style={{ color: sortField === "preco" ? "#54b4f7" : "#94a3b8" }} onClick={() => { setSortField("preco"); setSortAsc(!sortAsc); }}>Preço</th>
                  <th className="text-right py-3 px-2 cursor-pointer" style={{ color: sortField === "media" ? "#54b4f7" : "#94a3b8" }} onClick={() => { setSortField("media"); setSortAsc(!sortAsc); }}>Média</th>
                  <th className="text-right py-3 px-2" style={{ color: "#94a3b8" }}>Var</th>
                  <th className="text-right py-3 px-2" style={{ color: "#94a3b8" }}>M3</th>
                  <th className="text-right py-3 px-2" style={{ color: "#94a3b8" }}>M5</th>
                </tr>
              </thead>
              <tbody>
                {atletasFiltrados.slice(0, 100).map((a: any, i: number) => {
                  const pos = POSICOES[a.posicao_id] || "?";
                  const status = STATUS_JOGADOR[a.status_id];
                  const colors = POS_COLORS[pos];
                  return (
                    <tr key={a.atleta_id} className="cursor-pointer hover:opacity-80" onClick={() => setLocation(`/jogador/${a.atleta_id}`)}
                      style={{ borderBottom: "1px solid rgba(148, 163, 184, 0.08)" }}>
                      <td className="py-2 px-3 text-xs" style={{ color: "#64748b" }}>{i + 1}</td>
                      <td className="py-2 px-3 font-bold" style={{ color: "#f1f5f9" }}>{a.apelido}</td>
                      <td className="py-2 px-2 text-center">
                        <span className="text-xs font-bold px-2 py-0.5 rounded" style={{ background: colors?.bg, color: colors?.text }}>{pos}</span>
                      </td>
                      <td className="py-2 px-2"><ClubeBadge clubeId={a.clube_id} size={16} showName={false} /></td>
                      <td className="py-2 px-2 text-center">
                        {status && <span className="text-xs font-semibold" style={{ color: status.color }}>{status.label}</span>}
                      </td>
                      <td className="py-2 px-2 text-right font-bold" style={{ color: "#34d399" }}>{a.score?.toFixed(2)}</td>
                      <td className="py-2 px-2 text-right font-semibold" style={{ color: "#4da8f0" }}>C$ {a.preco?.toFixed(2)}</td>
                      <td className="py-2 px-2 text-right" style={{ color: "#f1f5f9" }}>{a.media?.toFixed(1)}</td>
                      <td className="py-2 px-2 text-right" style={{ color: (a.variacao_num || 0) >= 0 ? "#34d399" : "#f87171" }}>
                        {(a.variacao_num || 0) >= 0 ? "+" : ""}{a.variacao_num?.toFixed(2)}
                      </td>
                      <td className="py-2 px-2 text-right" style={{ color: "#94a3b8" }}>{a.media_ultimas_3?.toFixed(1)}</td>
                      <td className="py-2 px-2 text-right" style={{ color: "#94a3b8" }}>{a.media_ultimas_5?.toFixed(1)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function PlayerCard({ atleta, ranking, posNome, expanded, onToggle, onAnalise }: {
  atleta: any; ranking: number; posNome: string; expanded: boolean; onToggle: () => void; onAnalise: () => void;
}) {
  const colors = POS_COLORS[posNome];
  const status = STATUS_JOGADOR[atleta.status_id];
  const variacao = atleta.variacao_num || 0;

  return (
    <div className="rounded-xl overflow-hidden" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.1)" }}>
      {/* Main row */}
      <button onClick={onToggle} className="w-full flex items-center gap-3 p-3 hover:opacity-90 transition-opacity">
        {/* Ranking */}
        <span className="text-sm font-bold shrink-0" style={{ color: "#64748b", minWidth: 28 }}>#{ranking}</span>
        {/* Club badge */}
        <ClubeBadge clubeId={atleta.clube_id} size={24} showName={false} />
        {/* Name + club */}
        <div className="flex-1 text-left">
          <div className="flex items-center gap-2">
            <span className="font-bold" style={{ color: "#f1f5f9" }}>{atleta.apelido}</span>
            <span className="text-xs font-bold px-2 py-0.5 rounded" style={{ background: colors?.bg, color: colors?.text }}>{posNome}</span>
            {status && <span className="text-xs font-semibold" style={{ color: status.color }}>{status.label}</span>}
          </div>
          <span className="text-xs" style={{ color: "#64748b" }}>{atleta.clube_nome}</span>
        </div>
        {/* Stats */}
        <div className="flex items-center gap-4 shrink-0">
          <div className="text-right">
            <p className="text-xs" style={{ color: "#94a3b8" }}>Score</p>
            <p className="font-bold" style={{ color: "#34d399" }}>{atleta.score?.toFixed(2)}</p>
          </div>
          <div className="text-right">
            <p className="text-xs" style={{ color: "#94a3b8" }}>Preço</p>
            <p className="font-semibold" style={{ color: "#4da8f0" }}>C$ {atleta.preco?.toFixed(2)}</p>
          </div>
          <div className="text-right">
            <p className="text-xs" style={{ color: "#94a3b8" }}>Média</p>
            <p className="font-semibold" style={{ color: "#f1f5f9" }}>{atleta.media?.toFixed(1)}</p>
          </div>
          <div className="text-right">
            <p className="text-xs" style={{ color: "#94a3b8" }}>Var</p>
            <p className="font-semibold" style={{ color: variacao >= 0 ? "#34d399" : "#f87171" }}>
              {variacao >= 0 ? "↑" : "↓"} {variacao.toFixed(2)}
            </p>
          </div>
        </div>
      </button>

      {/* Expanded details - Streamlit style */}
      {expanded && (
        <div className="px-4 pb-4 space-y-3" style={{ borderTop: "1px solid rgba(148, 163, 184, 0.1)" }}>
          {/* Stats row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3">
            <MiniStat label="Média Geral" value={atleta.media?.toFixed(1)} color="#f1f5f9" />
            <MiniStat label="Últimas 3" value={atleta.media_ultimas_3?.toFixed(1)} color="#54b4f7" />
            <MiniStat label="Últimas 5" value={atleta.media_ultimas_5?.toFixed(1)} color="#FFC107" />
            <MiniStat label="Custo/Benefício" value={atleta.custo_beneficio?.toFixed(2)} color="#34d399" />
          </div>

          {/* Explicação */}
          {atleta.explicacao && (
            <div className="rounded-lg p-3" style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(148, 163, 184, 0.08)" }}>
              <p className="text-xs font-bold mb-1" style={{ color: "#94a3b8" }}>📝 Análise</p>
              {atleta.explicacao.resumo && <p className="text-sm" style={{ color: "#cbd5e1" }}>{atleta.explicacao.resumo}</p>}
              {atleta.explicacao.tendencia && (
                <p className="text-xs mt-1" style={{ color: "#64748b" }}>
                  Tendência: <span style={{ color: atleta.explicacao.tendencia === "alta" ? "#34d399" : atleta.explicacao.tendencia === "baixa" ? "#f87171" : "#FFC107" }}>
                    {atleta.explicacao.tendencia}
                  </span>
                </p>
              )}
              {atleta.explicacao.fatores && atleta.explicacao.fatores.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {atleta.explicacao.fatores.map((f: string, i: number) => (
                    <span key={i} className="text-xs px-2 py-0.5 rounded" style={{ background: "rgba(84, 180, 247, 0.1)", color: "#94a3b8" }}>{f}</span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Valorização prevista */}
          {atleta.valorizacao_prevista != null && (
            <div className="flex items-center gap-2 text-sm">
              <span style={{ color: atleta.valorizacao_prevista >= 0 ? "#34d399" : "#f87171", fontWeight: 600 }}>
                {atleta.valorizacao_prevista >= 0 ? "↑" : "↓"} C$ {Math.abs(atleta.valorizacao_prevista).toFixed(2)}
              </span>
              <span style={{ color: "#64748b" }}>valorização prevista</span>
            </div>
          )}

          <Button variant="outline" size="sm" onClick={onAnalise}
            style={{ borderColor: "rgba(84, 180, 247, 0.3)", color: "#54b4f7" }}>
            📊 Ver Análise Completa
          </Button>
        </div>
      )}
    </div>
  );
}

function MiniStat({ label, value, color }: { label: string; value?: string; color: string }) {
  return (
    <div className="rounded-lg p-2 text-center" style={{ background: "rgba(30, 41, 59, 0.4)" }}>
      <p className="text-xs" style={{ color: "#64748b" }}>{label}</p>
      <p className="font-bold text-lg" style={{ color }}>{value || "—"}</p>
    </div>
  );
}
