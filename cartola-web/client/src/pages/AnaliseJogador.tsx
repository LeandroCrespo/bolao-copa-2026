import { trpc } from "@/lib/trpc";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2, ArrowLeft } from "lucide-react";
import { useState, useMemo } from "react";
import { useParams, useLocation } from "wouter";
import {
  Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, ReferenceLine, Legend, Cell, ComposedChart,
} from "recharts";
import { ClubeBadge } from "@/components/ClubeBadge";

const POSICOES: Record<number, string> = { 1: "GOL", 2: "LAT", 3: "ZAG", 4: "MEI", 5: "ATA", 6: "TEC" };
const POS_COLORS: Record<string, string> = {
  GOL: "#EAB308", LAT: "#22C55E", ZAG: "#3B82F6", MEI: "#A855F7", ATA: "#EF4444", TEC: "#6B7280",
};
const COMP_COLORS: Record<string, string> = {
  'Brasileirão': '#54b4f7', 'Copa do Brasil': '#28A745', 'Libertadores': '#FFD700',
  'Sulamericana': '#FF6347', 'Paulista A1': '#FF69B4', 'Carioca': '#DDA0DD',
  'Mineiro': '#98FB98', 'Gaúcho': '#87CEEB', 'Baiano': '#F0E68C',
  'Paranaense': '#CD853F', 'Cearense': '#20B2AA', 'Goiano': '#9370DB', 'Pernambucano': '#FF7F50',
};
const COMP_ABREV: Record<string, string> = {
  'Copa do Brasil': 'CdB', 'Libertadores': 'Lib', 'Sulamericana': 'Sul',
  'Paulista A1': 'Pau', 'Carioca': 'Car', 'Mineiro': 'Min', 'Gaúcho': 'Gaú',
  'Brasileirão (paralelo)': 'Bra',
};

export default function AnaliseJogador() {
  const params = useParams<{ id?: string }>();
  const [, setLocation] = useLocation();
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedId, setSelectedId] = useState(params.id || "");

  const { data: atletas } = trpc.cartola.atletasMercado.useQuery();
  const { data: historicoCompleto, isLoading: loadingHist } = trpc.db.jogadorHistoricoCompleto.useQuery(
    { atletaId: selectedId, limite: 50 }, { enabled: !!selectedId }
  );
  const { data: historico } = trpc.db.jogadorHistorico.useQuery(
    { atletaId: selectedId, limite: 50 }, { enabled: !!selectedId }
  );

  const searchResults = useMemo(() => {
    if (!searchTerm || !atletas) return [];
    return atletas.filter((a: any) => a.apelido?.toLowerCase().includes(searchTerm.toLowerCase())).slice(0, 15);
  }, [searchTerm, atletas]);

  const jogadorMercado = useMemo(() => {
    if (!selectedId || !atletas) return null;
    return atletas.find((a: any) => String(a.atleta_id) === String(selectedId));
  }, [selectedId, atletas]);

  const jogador = historico?.[0] || jogadorMercado;

  // Combined chart data (Brasileirão + paralelas) - chronological order
  const combinedChartData = useMemo(() => {
    if (!historicoCompleto || !Array.isArray(historicoCompleto)) return [];
    return historicoCompleto.map((h: any, i: number) => {
      const comp = h.competicao || 'Brasileirão';
      const ano = h.ano || 2026;
      const rod = h.rodada;
      const dataJogo = h.data_jogo;
      const pontos = Number(h.pontos) || 0;
      let label: string;
      if (comp === 'Brasileirão') {
        label = rod != null ? `R${rod}/${String(ano).slice(-2)}` : `BR ${String(ano).slice(-2)}`;
      } else {
        const ca = COMP_ABREV[comp] || comp.substring(0, 3);
        if (dataJogo && rod == null) {
          try {
            const d = new Date(dataJogo);
            label = `${ca} ${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`;
          } catch { label = `${ca} ${i + 1}`; }
        } else if (rod != null) { label = `${ca} R${rod}`; }
        else { label = `${ca} ${i + 1}`; }
      }
      return { label, pontos, comp, color: COMP_COLORS[comp] || '#54b4f7', ano, rodada: rod };
    });
  }, [historicoCompleto]);

  // Moving averages on combined data
  const chartDataWithMA = useMemo(() => {
    return combinedChartData.map((d, i) => {
      const pts = combinedChartData.map(x => x.pontos);
      const avg = (start: number, end: number) => {
        const slice = pts.slice(start, end + 1);
        return slice.length > 0 ? slice.reduce((a, b) => a + b, 0) / slice.length : undefined;
      };
      return { ...d, ma3: i >= 2 ? avg(i - 2, i) : undefined, ma5: i >= 4 ? avg(i - 4, i) : undefined, ma10: i >= 9 ? avg(i - 9, i) : undefined };
    });
  }, [combinedChartData]);

  const chartDataLimited = useMemo(() => {
    if (chartDataWithMA.length <= 20) return chartDataWithMA;
    return chartDataWithMA.slice(-20);
  }, [chartDataWithMA]);

  const medias = useMemo(() => {
    if (!historico || !Array.isArray(historico) || historico.length === 0) return null;
    const pontos = historico.filter((h: any) => h.entrou_em_campo !== false).map((h: any) => Number(h.pontos) || 0);
    if (pontos.length === 0) return null;
    const avg = (arr: number[]) => arr.length > 0 ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
    return { geral: avg(pontos), ultimas3: avg(pontos.slice(0, 3)), ultimas5: avg(pontos.slice(0, 5)), ultimas10: avg(pontos.slice(0, 10)), maximo: Math.max(...pontos), minimo: Math.min(...pontos), jogos: pontos.length };
  }, [historico]);

  const scoutsTotais = useMemo(() => {
    if (!historico) return {};
    const totals: Record<string, number> = {};
    historico.forEach((h: any) => {
      if (h.gols) totals["G"] = (totals["G"] || 0) + h.gols;
      if (h.assistencias) totals["A"] = (totals["A"] || 0) + h.assistencias;
      if (h.desarmes) totals["DS"] = (totals["DS"] || 0) + h.desarmes;
      if (h.finalizacoes_gol) totals["FG"] = (totals["FG"] || 0) + h.finalizacoes_gol;
      if (h.defesas) totals["DE"] = (totals["DE"] || 0) + h.defesas;
      if (h.cartao_amarelo) totals["CA"] = (totals["CA"] || 0) + h.cartao_amarelo;
      if (h.cartao_vermelho) totals["CV"] = (totals["CV"] || 0) + h.cartao_vermelho;
      if (h.gols_sofridos) totals["GS"] = (totals["GS"] || 0) + h.gols_sofridos;
      if (h.faltas_cometidas) totals["FC"] = (totals["FC"] || 0) + h.faltas_cometidas;
      if (h.faltas_sofridas) totals["FS"] = (totals["FS"] || 0) + h.faltas_sofridas;
    });
    return totals;
  }, [historico]);

  const compStats = useMemo(() => {
    if (!historicoCompleto) return null;
    const brasileiro = historicoCompleto.filter((h: any) => h.competicao === 'Brasileirão').length;
    const paralelas = historicoCompleto.filter((h: any) => h.competicao !== 'Brasileirão');
    const compNames = Array.from(new Set(paralelas.map((p: any) => p.competicao)));
    return { brasileiro, paralelo: paralelas.length, compNames };
  }, [historicoCompleto]);

  const handleSelectPlayer = (id: string) => { setSelectedId(id); setSearchTerm(""); setLocation(`/jogador/${id}`); };
  const loading = loadingHist;
  const posNome = POSICOES[jogador?.posicao_id as number] || "?";
  const posColor = POS_COLORS[posNome] || "#94a3b8";

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        {selectedId && (
          <Button variant="ghost" size="sm" onClick={() => { setSelectedId(""); setLocation("/jogador"); }} style={{ color: "#94a3b8" }}>
            <ArrowLeft className="h-4 w-4 mr-1" /> Voltar
          </Button>
        )}
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "#f1f5f9" }}>🔍 Análise Individual de Jogador</h1>
          <p className="text-sm mt-1" style={{ color: "#94a3b8" }}>Histórico completo, médias móveis e projeções</p>
        </div>
      </div>

      <div className="rounded-xl p-4" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: "#64748b" }}>🔍</span>
          <Input placeholder="Buscar jogador por nome..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-10"
            style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(148, 163, 184, 0.2)", color: "#f1f5f9" }} />
        </div>
        {searchResults.length > 0 && (
          <div className="mt-2 rounded-lg overflow-hidden max-h-[300px] overflow-y-auto" style={{ border: "1px solid rgba(148, 163, 184, 0.15)" }}>
            {searchResults.map((a: any) => (
              <button key={a.atleta_id} onClick={() => handleSelectPlayer(String(a.atleta_id))}
                className="w-full flex items-center gap-3 p-3 text-left transition-colors" style={{ borderBottom: "1px solid rgba(148, 163, 184, 0.08)" }}
                onMouseEnter={(e) => e.currentTarget.style.background = "rgba(84, 180, 247, 0.1)"}
                onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}>
                <ClubeBadge clubeId={a.clube_id} size={20} showName={false} />
                <span className="font-bold" style={{ color: "#f1f5f9" }}>{a.apelido}</span>
                <span className="text-xs font-bold px-2 py-0.5 rounded ml-auto"
                  style={{ background: `${POS_COLORS[POSICOES[a.posicao_id]] || "#6B7280"}22`, color: POS_COLORS[POSICOES[a.posicao_id]] || "#6B7280" }}>
                  {POSICOES[a.posicao_id]}
                </span>
                <span className="text-sm" style={{ color: "#4da8f0" }}>C$ {a.preco?.toFixed(2)}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {!selectedId ? (
        <div className="rounded-xl p-12 text-center" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
          <p className="text-4xl mb-4">⚽</p>
          <p style={{ color: "#94a3b8" }}>Selecione um jogador para ver a análise completa</p>
        </div>
      ) : loading ? (
        <div className="flex items-center justify-center min-h-[40vh]"><Loader2 className="h-8 w-8 animate-spin" style={{ color: "#54b4f7" }} /></div>
      ) : (
        <>
          {jogador && (
            <div className="rounded-xl p-5" style={{ background: "linear-gradient(135deg, #1a2744 0%, #0b1d33 100%)", border: "1px solid rgba(84, 180, 247, 0.3)", boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)" }}>
              <div className="flex items-start justify-between flex-wrap gap-4">
                <div className="flex items-center gap-4">
                  {jogadorMercado?.foto && (
                    <img src={String(jogadorMercado.foto).replace("FORMATO", "140x140")} alt={jogador.apelido} className="h-16 w-16 rounded-full" style={{ border: `2px solid ${posColor}` }} />
                  )}
                  <div>
                    <div className="flex items-center gap-3">
                      <h2 className="text-xl font-bold" style={{ color: "#f1f5f9" }}>{jogador.apelido}</h2>
                      <span className="text-xs font-bold px-2 py-0.5 rounded" style={{ background: `${posColor}22`, color: posColor }}>{posNome}</span>
                    </div>
                    <div className="flex items-center gap-2 mt-1"><ClubeBadge clubeId={jogador.clube_id || jogadorMercado?.clube_id} size={20} /></div>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            <MetricCard label="PREÇO" value={`C$ ${Number(jogador?.preco || jogadorMercado?.preco)?.toFixed(2)}`} color="#54b4f7" />
            <MetricCard label="MÉDIA CARTOLA" value={Number(jogador?.media || jogadorMercado?.media)?.toFixed(2) || "—"} color="#FFC107" />
            <MetricCard label="MÉDIA 3R" value={medias?.ultimas3.toFixed(2) || "—"} color="#98FB98" />
            <MetricCard label="PREVISÃO" value={(jogadorMercado as any)?.pontuacao_esperada?.toFixed(2) || medias?.geral.toFixed(2) || "—"} color="#28A745" />
            <MetricCard label="JOGOS" value={String(medias?.jogos || 0)} color="#FF69B4" />
          </div>

          {chartDataLimited.length > 0 && (
            <div className="rounded-xl p-4" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
              <p className="font-bold mb-3" style={{ color: "#f1f5f9" }}>📈 Histórico de Pontuação</p>
              <ResponsiveContainer width="100%" height={380}>
                <ComposedChart data={chartDataLimited} barCategoryGap="20%">
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
                  <XAxis dataKey="label" stroke="#64748b" fontSize={9} angle={-45} textAnchor="end" height={70} interval={0} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip contentStyle={{ backgroundColor: "#1e293b", border: "1px solid rgba(148, 163, 184, 0.2)", borderRadius: "8px", color: "#f1f5f9" }}
                    formatter={(value: number, name: string) => [value?.toFixed(1), name]}
                    labelFormatter={(label) => { const item = chartDataLimited.find(d => d.label === label); return item ? `${label} (${item.comp})` : label; }} />
                  <Legend wrapperStyle={{ color: "#94a3b8" }} />
                  <Bar dataKey="pontos" name="Pontos" radius={[3, 3, 0, 0]} opacity={0.7}>
                    {chartDataLimited.map((entry, index) => (<Cell key={index} fill={entry.color} />))}
                  </Bar>
                  <Line dataKey="ma10" name="MM 10R" stroke="rgba(152, 251, 152, 0.5)" strokeWidth={1.5} strokeDasharray="3 3" dot={false} type="monotone" />
                  <Line dataKey="ma5" name="MM 5R" stroke="rgba(255, 193, 7, 0.7)" strokeWidth={2} strokeDasharray="5 5" dot={false} type="monotone" />
                  <Line dataKey="ma3" name="MM 3R" stroke="#FF69B4" strokeWidth={3} dot={false} type="monotone" />
                  {medias && <ReferenceLine y={medias.geral} stroke="rgba(255,255,255,0.2)" strokeDasharray="5 5"
                    label={{ value: `Média: ${medias.geral.toFixed(1)}`, fill: "rgba(255,255,255,0.4)", fontSize: 10, position: "right" }} />}
                </ComposedChart>
              </ResponsiveContainer>
              {compStats && compStats.paralelo > 0 && (
                <p className="text-center text-xs mt-1" style={{ color: "#6C757D" }}>
                  📊 {compStats.brasileiro} jogos do Brasileirão + {compStats.paralelo} de competições paralelas ({compStats.compNames.join(", ")})
                </p>
              )}
            </div>
          )}

          {medias && (
            <div className="rounded-xl p-4" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
              <p className="font-bold mb-3" style={{ color: "#f1f5f9" }}>📊 Comparativo de Médias</p>
              <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
                <StatCard label="MÉDIA GERAL" value={medias.geral.toFixed(1)} color="#f1f5f9" />
                <StatCard label="ÚLTIMAS 3" value={medias.ultimas3.toFixed(1)} color="#54b4f7" highlight />
                <StatCard label="ÚLTIMAS 5" value={medias.ultimas5.toFixed(1)} color="#FFC107" />
                <StatCard label="ÚLTIMAS 10" value={medias.ultimas10.toFixed(1)} color="#f1f5f9" />
                <StatCard label="MÁXIMO" value={medias.maximo.toFixed(1)} color="#34d399" />
                <StatCard label="MÍNIMO" value={medias.minimo.toFixed(1)} color="#f87171" />
                <StatCard label="JOGOS" value={String(medias.jogos)} color="#f1f5f9" />
              </div>
            </div>
          )}

          {historico && historico.length > 0 && (
            <div className="rounded-xl p-4" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
              <p className="font-bold mb-3" style={{ color: "#f1f5f9" }}>💰 Evolução do Preço</p>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={[...historico].reverse().map((h: any) => ({ label: `R${h.rodada}/${String(h.ano).slice(-2)}`, preco: Number(h.preco) || 0 }))}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
                  <XAxis dataKey="label" stroke="#64748b" fontSize={11} angle={-45} textAnchor="end" height={60} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip contentStyle={{ backgroundColor: "#1e293b", border: "1px solid rgba(148, 163, 184, 0.2)", borderRadius: "8px", color: "#f1f5f9" }} />
                  <Line dataKey="preco" name="Preço" stroke="#FFC107" strokeWidth={2} dot={{ r: 3, fill: "#FFC107" }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {Object.keys(scoutsTotais).length > 0 && (
            <div className="rounded-xl p-4" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
              <p className="font-bold mb-3" style={{ color: "#f1f5f9" }}>🎯 Scouts Acumulados</p>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                {Object.entries(scoutsTotais).sort(([, a], [, b]) => b - a).map(([scout, total]) => {
                  const isPositive = ["G", "A", "DS", "FG", "DE", "FS", "SG", "PD"].includes(scout);
                  return (
                    <div key={scout} className="rounded-lg p-3 text-center" style={{ background: "rgba(30, 41, 59, 0.5)" }}>
                      <p className="text-2xl font-bold" style={{ color: isPositive ? "#34d399" : "#f87171" }}>{total}</p>
                      <p className="text-xs" style={{ color: "#94a3b8" }}>{scoutLabel(scout)}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {historico && historico.length > 0 && (
            <div className="rounded-xl overflow-hidden" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
              <div className="p-4"><p className="font-bold" style={{ color: "#f1f5f9" }}>📋 Histórico Brasileirão ({historico.length} rodadas)</p></div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr style={{ borderBottom: "1px solid rgba(148, 163, 184, 0.15)" }}>
                      <th className="text-left py-3 px-3" style={{ color: "#94a3b8" }}>Rodada</th>
                      <th className="text-right py-3 px-2" style={{ color: "#94a3b8" }}>Pontos</th>
                      <th className="text-right py-3 px-2" style={{ color: "#94a3b8" }}>Média</th>
                      <th className="text-right py-3 px-2" style={{ color: "#94a3b8" }}>Preço</th>
                      <th className="text-right py-3 px-2" style={{ color: "#94a3b8" }}>Variação</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historico.map((h: any, i: number) => (
                      <tr key={i} style={{ borderBottom: "1px solid rgba(148, 163, 184, 0.08)" }}>
                        <td className="py-2 px-3 font-bold" style={{ color: "#f1f5f9" }}>R{h.rodada} ({h.ano})</td>
                        <td className="py-2 px-2 text-right font-bold" style={{ color: (Number(h.pontos) || 0) >= 0 ? "#34d399" : "#f87171" }}>{Number(h.pontos)?.toFixed(1)}</td>
                        <td className="py-2 px-2 text-right" style={{ color: "#f1f5f9" }}>{Number(h.media)?.toFixed(1)}</td>
                        <td className="py-2 px-2 text-right" style={{ color: "#4da8f0" }}>C$ {Number(h.preco)?.toFixed(2)}</td>
                        <td className="py-2 px-2 text-right" style={{ color: (Number(h.variacao) || 0) >= 0 ? "#34d399" : "#f87171" }}>
                          {(Number(h.variacao) || 0) >= 0 ? "+" : ""}{Number(h.variacao)?.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function MetricCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="rounded-xl p-3 text-center" style={{ background: "#0b1d33", borderTop: `3px solid ${color}` }}>
      <p className="text-[0.75rem] uppercase" style={{ color: "#ADB5BD" }}>{label}</p>
      <p className="text-xl font-bold mt-1" style={{ color }}>{value}</p>
    </div>
  );
}

function StatCard({ label, value, color, highlight }: { label: string; value: string; color: string; highlight?: boolean }) {
  return (
    <div className="rounded-xl p-3 text-center" style={{ background: "rgba(15, 23, 42, 0.6)", border: highlight ? "1px solid rgba(84, 180, 247, 0.3)" : "1px solid rgba(148, 163, 184, 0.1)" }}>
      <p className="text-[10px] uppercase tracking-wider" style={{ color: "#64748b" }}>{label}</p>
      <p className="text-xl font-bold mt-0.5" style={{ color }}>{value}</p>
    </div>
  );
}

function scoutLabel(scout: string): string {
  const labels: Record<string, string> = {
    G: "Gols", A: "Assistências", DS: "Desarmes", FG: "Finaliz. Gol",
    DE: "Defesas", CA: "Cartão Amarelo", CV: "Cartão Vermelho",
    GS: "Gols Sofridos", FC: "Faltas Comet.", FS: "Faltas Sofridas",
    SG: "Saldo de Gols", PP: "Pênalti Perdido", PD: "Pênalti Defendido",
  };
  return labels[scout] || scout;
}
