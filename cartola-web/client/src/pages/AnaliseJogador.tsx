import { trpc } from "@/lib/trpc";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Loader2, ArrowLeft } from "lucide-react";
import { useState, useMemo } from "react";
import { useParams, useLocation } from "wouter";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, ReferenceLine, Legend, Cell,
} from "recharts";
import { ClubeBadge } from "@/components/ClubeBadge";

const POSICOES: Record<number, string> = { 1: "GOL", 2: "LAT", 3: "ZAG", 4: "MEI", 5: "ATA", 6: "TEC" };
const POS_COLORS: Record<string, string> = {
  GOL: "#EAB308", LAT: "#22C55E", ZAG: "#3B82F6", MEI: "#A855F7", ATA: "#EF4444", TEC: "#6B7280",
};

export default function AnaliseJogador() {
  const params = useParams<{ id?: string }>();
  const [, setLocation] = useLocation();
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedId, setSelectedId] = useState(params.id || "");

  const { data: atletas } = trpc.cartola.atletasMercado.useQuery();
  const { data: historico, isLoading: loadingHist } = trpc.db.jogadorHistorico.useQuery(
    { atletaId: selectedId, limite: 50 },
    { enabled: !!selectedId }
  );
  const { data: paralelas, isLoading: loadingPar } = trpc.db.competParalelas.useQuery(
    { atletaId: selectedId },
    { enabled: !!selectedId }
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

  // Chart data - reversed so oldest first
  const chartData = useMemo(() => {
    if (!historico || !Array.isArray(historico)) return [];
    return [...historico].reverse().map((h: any) => ({
      label: `R${h.rodada}`,
      pontos: Number(h.pontos) || 0,
      media: Number(h.media) || 0,
      preco: Number(h.preco) || 0,
      ano: h.ano,
    }));
  }, [historico]);

  // Moving averages
  const chartDataWithMA = useMemo(() => {
    return chartData.map((d, i) => {
      const slice3 = chartData.slice(Math.max(0, i - 2), i + 1);
      const slice5 = chartData.slice(Math.max(0, i - 4), i + 1);
      const slice10 = chartData.slice(Math.max(0, i - 9), i + 1);
      const avg = (arr: typeof chartData) => arr.reduce((s, x) => s + x.pontos, 0) / arr.length;
      return {
        ...d,
        ma3: slice3.length >= 3 ? avg(slice3) : undefined,
        ma5: slice5.length >= 5 ? avg(slice5) : undefined,
        ma10: slice10.length >= 10 ? avg(slice10) : undefined,
      };
    });
  }, [chartData]);

  // Averages
  const medias = useMemo(() => {
    if (!historico || !Array.isArray(historico) || historico.length === 0) return null;
    const pontos = historico.filter((h: any) => h.entrou_em_campo !== false).map((h: any) => Number(h.pontos) || 0);
    if (pontos.length === 0) return null;
    const avg = (arr: number[]) => arr.length > 0 ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
    return {
      geral: avg(pontos),
      ultimas3: avg(pontos.slice(0, 3)),
      ultimas5: avg(pontos.slice(0, 5)),
      ultimas10: avg(pontos.slice(0, 10)),
      maximo: Math.max(...pontos),
      minimo: Math.min(...pontos),
      jogos: pontos.length,
    };
  }, [historico]);

  // Scouts summary
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

  const handleSelectPlayer = (id: string) => {
    setSelectedId(id);
    setSearchTerm("");
    setLocation(`/jogador/${id}`);
  };

  const loading = loadingHist || loadingPar;
  const posNome = POSICOES[jogador?.posicao_id as number] || "?";
  const posColor = POS_COLORS[posNome] || "#94a3b8";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        {selectedId && (
          <Button variant="ghost" size="sm" onClick={() => { setSelectedId(""); setLocation("/jogador"); }}
            style={{ color: "#94a3b8" }}>
            <ArrowLeft className="h-4 w-4 mr-1" /> Voltar
          </Button>
        )}
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "#f1f5f9" }}>📊 Análise de Jogador</h1>
          <p className="text-sm mt-1" style={{ color: "#94a3b8" }}>Histórico de pontuações, scouts e competições paralelas</p>
        </div>
      </div>

      {/* Search */}
      <div className="rounded-xl p-4" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: "#64748b" }}>🔍</span>
          <Input placeholder="Buscar jogador por nome..." value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)} className="pl-10"
            style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(148, 163, 184, 0.2)", color: "#f1f5f9" }} />
        </div>
        {searchResults.length > 0 && (
          <div className="mt-2 rounded-lg overflow-hidden max-h-[300px] overflow-y-auto"
            style={{ border: "1px solid rgba(148, 163, 184, 0.15)" }}>
            {searchResults.map((a: any) => (
              <button key={a.atleta_id} onClick={() => handleSelectPlayer(String(a.atleta_id))}
                className="w-full flex items-center gap-3 p-3 text-left transition-colors"
                style={{ borderBottom: "1px solid rgba(148, 163, 184, 0.08)" }}
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
        <div className="flex items-center justify-center min-h-[40vh]">
          <Loader2 className="h-8 w-8 animate-spin" style={{ color: "#54b4f7" }} />
        </div>
      ) : (
        <>
          {/* Player Header - Streamlit style */}
          {jogador && (
            <div className="rounded-xl p-5" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
              <div className="flex items-start justify-between flex-wrap gap-4">
                <div className="flex items-center gap-4">
                  {jogadorMercado?.foto && (
                    <img src={String(jogadorMercado.foto).replace("FORMATO", "140x140")} alt={jogador.apelido}
                      className="h-16 w-16 rounded-full" style={{ border: `2px solid ${posColor}` }} />
                  )}
                  <div>
                    <div className="flex items-center gap-3">
                      <h2 className="text-xl font-bold" style={{ color: "#f1f5f9" }}>{jogador.apelido}</h2>
                      <span className="text-xs font-bold px-2 py-0.5 rounded" style={{ background: `${posColor}22`, color: posColor }}>{posNome}</span>
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <ClubeBadge clubeId={jogador.clube_id || jogadorMercado?.clube_id} size={20} />
                    </div>
                  </div>
                </div>
                <div className="flex gap-6 text-center">
                  <div>
                    <p className="text-2xl font-bold" style={{ color: "#54b4f7" }}>{medias?.geral.toFixed(1) || "—"}</p>
                    <p className="text-xs" style={{ color: "#94a3b8" }}>Média</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold" style={{ color: "#f1f5f9" }}>{medias?.jogos || 0}</p>
                    <p className="text-xs" style={{ color: "#94a3b8" }}>Jogos</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold" style={{ color: "#34d399" }}>C$ {Number(jogador.preco || jogadorMercado?.preco)?.toFixed(2)}</p>
                    <p className="text-xs" style={{ color: "#94a3b8" }}>Preço</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Averages - Streamlit style colored cards */}
          {medias && (
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
              <StatCard label="MÉDIA GERAL" value={medias.geral.toFixed(1)} color="#f1f5f9" />
              <StatCard label="ÚLTIMAS 3" value={medias.ultimas3.toFixed(1)} color="#54b4f7" highlight />
              <StatCard label="ÚLTIMAS 5" value={medias.ultimas5.toFixed(1)} color="#FFC107" />
              <StatCard label="ÚLTIMAS 10" value={medias.ultimas10.toFixed(1)} color="#f1f5f9" />
              <StatCard label="MÁXIMO" value={medias.maximo.toFixed(1)} color="#34d399" />
              <StatCard label="MÍNIMO" value={medias.minimo.toFixed(1)} color="#f87171" />
              <StatCard label="JOGOS" value={String(medias.jogos)} color="#f1f5f9" />
            </div>
          )}

          <Tabs defaultValue="historico" className="w-full">
            <TabsList className="grid w-full grid-cols-3" style={{ background: "rgba(15, 23, 42, 0.6)" }}>
              <TabsTrigger value="historico">Histórico</TabsTrigger>
              <TabsTrigger value="scouts">Scouts</TabsTrigger>
              <TabsTrigger value="paralelas">Comp. Paralelas</TabsTrigger>
            </TabsList>

            {/* Histórico Tab */}
            <TabsContent value="historico" className="space-y-4">
              {chartDataWithMA.length > 0 ? (
                <>
                  {/* Bar chart with colored bars + moving averages */}
                  <div className="rounded-xl p-4" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
                    <p className="font-bold mb-3" style={{ color: "#f1f5f9" }}>📊 Pontuação por Rodada</p>
                    <ResponsiveContainer width="100%" height={350}>
                      <BarChart data={chartDataWithMA} barCategoryGap="15%">
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
                        <XAxis dataKey="label" stroke="#64748b" fontSize={11} angle={-45} textAnchor="end" height={60} />
                        <YAxis stroke="#64748b" fontSize={11} />
                        <Tooltip
                          contentStyle={{ backgroundColor: "#1e293b", border: "1px solid rgba(148, 163, 184, 0.2)", borderRadius: "8px", color: "#f1f5f9" }}
                          formatter={(value: number, name: string) => [value?.toFixed(1), name]}
                        />
                        <Legend wrapperStyle={{ color: "#94a3b8" }} />
                        <Bar dataKey="pontos" name="Pontos" radius={[4, 4, 0, 0]}>
                          {chartDataWithMA.map((entry, index) => (
                            <Cell key={index} fill={entry.pontos >= 0 ? "#54b4f7" : "#f87171"} />
                          ))}
                        </Bar>
                        <Line dataKey="ma3" name="Média 3R" stroke="#FFC107" strokeWidth={2} dot={false} type="monotone" />
                        <Line dataKey="ma5" name="Média 5R" stroke="#34d399" strokeWidth={2} dot={false} type="monotone" />
                        {medias && <ReferenceLine y={medias.geral} stroke="#f87171" strokeDasharray="5 5" label={{ value: `Média: ${medias.geral.toFixed(1)}`, fill: "#f87171", fontSize: 11 }} />}
                      </BarChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Price evolution */}
                  <div className="rounded-xl p-4" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
                    <p className="font-bold mb-3" style={{ color: "#f1f5f9" }}>💰 Evolução do Preço</p>
                    <ResponsiveContainer width="100%" height={250}>
                      <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
                        <XAxis dataKey="label" stroke="#64748b" fontSize={11} angle={-45} textAnchor="end" height={60} />
                        <YAxis stroke="#64748b" fontSize={11} />
                        <Tooltip contentStyle={{ backgroundColor: "#1e293b", border: "1px solid rgba(148, 163, 184, 0.2)", borderRadius: "8px", color: "#f1f5f9" }} />
                        <Line dataKey="preco" name="Preço" stroke="#FFC107" strokeWidth={2} dot={{ r: 3, fill: "#FFC107" }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>

                  {/* History Table */}
                  <div className="rounded-xl overflow-hidden" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
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
                          {historico!.map((h: any, i: number) => (
                            <tr key={i} style={{ borderBottom: "1px solid rgba(148, 163, 184, 0.08)" }}>
                              <td className="py-2 px-3 font-bold" style={{ color: "#f1f5f9" }}>R{h.rodada} ({h.ano})</td>
                              <td className="py-2 px-2 text-right font-bold" style={{ color: (Number(h.pontos) || 0) >= 0 ? "#34d399" : "#f87171" }}>
                                {Number(h.pontos)?.toFixed(1)}
                              </td>
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
                </>
              ) : (
                <div className="rounded-xl p-8 text-center" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
                  <p className="text-4xl mb-3">📉</p>
                  <p style={{ color: "#94a3b8" }}>Sem dados históricos para este jogador</p>
                </div>
              )}
            </TabsContent>

            {/* Scouts Tab */}
            <TabsContent value="scouts" className="space-y-4">
              {Object.keys(scoutsTotais).length > 0 ? (
                <div className="rounded-xl p-4" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
                  <p className="font-bold mb-3" style={{ color: "#f1f5f9" }}>🎯 Scouts Acumulados</p>
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                    {Object.entries(scoutsTotais)
                      .sort(([, a], [, b]) => b - a)
                      .map(([scout, total]) => {
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
              ) : (
                <div className="rounded-xl p-8 text-center" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
                  <p className="text-4xl mb-3">🎯</p>
                  <p style={{ color: "#94a3b8" }}>Sem dados de scouts disponíveis</p>
                </div>
              )}
            </TabsContent>

            {/* Paralelas Tab */}
            <TabsContent value="paralelas" className="space-y-4">
              {paralelas && paralelas.length > 0 ? (
                <div className="rounded-xl overflow-hidden" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
                  <div className="p-4">
                    <p className="font-bold" style={{ color: "#f1f5f9" }}>🏆 Competições Paralelas ({paralelas.length} jogos)</p>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr style={{ borderBottom: "1px solid rgba(148, 163, 184, 0.15)" }}>
                          <th className="text-left py-3 px-3" style={{ color: "#94a3b8" }}>Data</th>
                          <th className="text-left py-3 px-2" style={{ color: "#94a3b8" }}>Competição</th>
                          <th className="text-left py-3 px-2" style={{ color: "#94a3b8" }}>Adversário</th>
                          <th className="text-right py-3 px-2" style={{ color: "#94a3b8" }}>Pts Sim.</th>
                          <th className="text-right py-3 px-2" style={{ color: "#94a3b8" }}>G</th>
                          <th className="text-right py-3 px-2" style={{ color: "#94a3b8" }}>A</th>
                          <th className="text-right py-3 px-2" style={{ color: "#94a3b8" }}>Min</th>
                        </tr>
                      </thead>
                      <tbody>
                        {paralelas.map((p: any, i: number) => (
                          <tr key={i} style={{ borderBottom: "1px solid rgba(148, 163, 184, 0.08)" }}>
                            <td className="py-2 px-3" style={{ color: "#f1f5f9" }}>{p.data_jogo ? new Date(p.data_jogo).toLocaleDateString("pt-BR") : "—"}</td>
                            <td className="py-2 px-2">
                              <span className="text-xs font-bold px-2 py-0.5 rounded" style={{ background: "rgba(168, 85, 247, 0.15)", color: "#A855F7" }}>{p.competicao}</span>
                            </td>
                            <td className="py-2 px-2" style={{ color: "#f1f5f9" }}>{p.adversario || "—"}</td>
                            <td className="py-2 px-2 text-right font-bold" style={{ color: (Number(p.pontuacao_simulada) || 0) >= 0 ? "#34d399" : "#f87171" }}>
                              {Number(p.pontuacao_simulada)?.toFixed(1)}
                            </td>
                            <td className="py-2 px-2 text-right" style={{ color: "#f1f5f9" }}>{p.gols || 0}</td>
                            <td className="py-2 px-2 text-right" style={{ color: "#f1f5f9" }}>{p.assistencias || 0}</td>
                            <td className="py-2 px-2 text-right" style={{ color: "#94a3b8" }}>{p.minutos_jogados || 0}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="rounded-xl p-8 text-center" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
                  <p className="text-4xl mb-3">🏆</p>
                  <p style={{ color: "#94a3b8" }}>Sem dados de competições paralelas</p>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </>
      )}
    </div>
  );
}

function StatCard({ label, value, color, highlight }: { label: string; value: string; color: string; highlight?: boolean }) {
  return (
    <div className="rounded-xl p-3 text-center" style={{
      background: "rgba(15, 23, 42, 0.6)",
      border: highlight ? "1px solid rgba(84, 180, 247, 0.3)" : "1px solid rgba(148, 163, 184, 0.1)",
    }}>
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
