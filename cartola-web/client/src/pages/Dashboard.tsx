import { trpc } from "@/lib/trpc";
import { Loader2 } from "lucide-react";
import { useLocation } from "wouter";
import { useMemo } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend, LabelList,
  ResponsiveContainer, Line, ComposedChart, ReferenceLine, Cell,
} from "recharts";
import { ClubeBadge } from "@/components/ClubeBadge";

const DERVE_LOGO = "https://d2xsxph8kpxj0f.cloudfront.net/310419663031516744/oTZR9ZkHbDCNQCXXcPwoHW/distintivo_derve_final_400_9982f663.png";
const CAMISA_URL = "https://d2xsxph8kpxj0f.cloudfront.net/310419663031516744/oTZR9ZkHbDCNQCXXcPwoHW/camisa_derve_bc758971.png";

export default function Dashboard() {
  const [, setLocation] = useLocation();
  const { data: mercado, isLoading: loadingMercado } = trpc.cartola.mercadoStatus.useQuery();
  const { data: escalacoes } = trpc.estrategia.listarEscalacoes.useQuery({ ano: new Date().getFullYear() });
  const { data: partidas } = trpc.cartola.partidas.useQuery();
  const { data: escalacaoAtual } = trpc.estrategia.escalacaoAtual.useQuery();

  const anoAtual = new Date().getFullYear();
  const rodadaAtual = mercado?.rodada_atual || 0;

  // Calculate metrics from current year escalações (same as Streamlit)
  const metricas = useMemo(() => {
    if (!escalacoes || !Array.isArray(escalacoes)) return null;
    const processadas = escalacoes
      .filter((e: any) => e.pontos_reais != null && parseFloat(e.pontos_reais) > 0)
      .sort((a: any, b: any) => a.rodada - b.rodada);
    if (processadas.length === 0) return null;

    const totalPontos = processadas.reduce((s: number, e: any) => s + parseFloat(e.pontos_reais), 0);
    const rodadasJogadas = processadas.length;
    const media = totalPontos / rodadasJogadas;
    const melhor = processadas.reduce((best: any, e: any) =>
      parseFloat(e.pontos_reais) > parseFloat(best.pontos_reais) ? e : best, processadas[0]);

    // Patrimônio: orcamento_disponivel da última rodada + valorização da última rodada
    // Streamlit: orcamento_atual = orcamento_disponivel(last) + valorizacao_com_sub(last)
    const ultima = processadas[processadas.length - 1];
    const orcDisp = parseFloat(String(ultima.orcamento_disponivel ?? ultima.orcamento ?? ultima.custo_total ?? "100"));
    const lastVal = parseFloat(ultima.valorizacao_com_sub) || 0;
    const orcamento = orcDisp + lastVal;
    const totalVal = processadas.reduce((s: number, e: any) => s + (parseFloat(e.valorizacao_com_sub) || 0), 0);

    // Build chart data
    const chartData = processadas.map((e: any) => ({
      rodada: `R${e.rodada}`,
      real: parseFloat(e.pontos_reais) || 0,
      previsto: parseFloat(e.pontuacao_prevista) || parseFloat(e.pontuacao_esperada) || 0,
    }));

    return {
      totalPontos: Math.round(totalPontos * 10) / 10,
      rodadasJogadas,
      media: Math.round(media * 10) / 10,
      patrimonio: Math.round(orcamento * 10) / 10,
      patrimonioVar: Math.round((orcamento - 100) * 10) / 10,
      totalValorizacao: Math.round(totalVal * 10) / 10,
      melhorPontos: Math.round(parseFloat(melhor.pontos_reais) * 10) / 10,
      melhorRodada: melhor.rodada,
      chartData,
    };
  }, [escalacoes]);

  // Status badge
  const statusBadge = useMemo(() => {
    if (!mercado) return { text: "CARREGANDO", bg: "#6C757D" };
    if (mercado.game_over) return { text: "TEMPORADA ENCERRADA", bg: "#6C757D" };
    if (mercado.status_mercado === 1) return { text: "MERCADO ABERTO", bg: "#28a745" };
    return { text: "MERCADO FECHADO", bg: "#dc3545" };
  }, [mercado]);

  // Group partidas by date/time
  const partidasAgrupadas = useMemo(() => {
    if (!partidas || !Array.isArray(partidas)) return [];
    const grupos: { label: string; jogos: any[] }[] = [];
    const map = new Map<string, any[]>();
    for (const p of partidas) {
      let label = "Horário indefinido";
      if (p.partida_data) {
        try {
          const dt = new Date(p.partida_data);
          const dias: Record<string, string> = { Sun: "Dom", Mon: "Seg", Tue: "Ter", Wed: "Qua", Thu: "Qui", Fri: "Sex", Sat: "Sáb" };
          const dia = dias[dt.toLocaleDateString("en-US", { weekday: "short" })] || "";
          label = `${String(dt.getDate()).padStart(2, "0")}/${String(dt.getMonth() + 1).padStart(2, "0")} (${dia}) - ${String(dt.getHours()).padStart(2, "0")}h${String(dt.getMinutes()).padStart(2, "0")}`;
        } catch { /* keep default */ }
      }
      if (!map.has(label)) {
        map.set(label, []);
        grupos.push({ label, jogos: map.get(label)! });
      }
      map.get(label)!.push(p);
    }
    return grupos;
  }, [partidas]);

  const nValidos = partidas?.filter((p: any) => p.valida !== false).length || 0;
  const nTotal = partidas?.length || 0;

  return (
    <div className="space-y-5 max-w-5xl mx-auto">
      {/* Header - centered like Streamlit */}
      <div className="text-center py-4">
        <div className="flex items-center justify-center gap-3 mb-1">
          <img src={DERVE_LOGO} alt="Dervé FC" className="h-10 w-10 object-contain" />
          <h1 className="text-3xl font-bold" style={{ color: "#54b4f7", fontFamily: "var(--font-heading)" }}>
            Dervé FC
          </h1>
        </div>
        <p className="text-sm" style={{ color: "#6C757D" }}>Dashboard — Temporada {anoAtual}</p>
      </div>

      {loadingMercado ? (
        <div className="flex items-center justify-center min-h-[30vh]">
          <Loader2 className="h-8 w-8 animate-spin" style={{ color: "#54b4f7" }} />
        </div>
      ) : (
        <>
          {/* Rodada Status Bar */}
          <div className="rounded-xl p-4" style={{ background: "rgba(15, 25, 50, 0.6)", border: "1px solid rgba(77, 168, 240, 0.2)" }}>
            <div className="flex items-center justify-between flex-wrap gap-2">
              <span className="text-xl font-bold" style={{ color: "#54b4f7" }}>Rodada {rodadaAtual}</span>
              <span className="text-xs font-bold px-3 py-1.5 rounded-full text-white" style={{ background: statusBadge.bg }}>
                {statusBadge.text}
              </span>
            </div>
          </div>

          {/* 4 Metric Cards - exactly like Streamlit */}
          {metricas && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {/* PONTOS TOTAIS */}
              <div className="rounded-xl p-3 text-center" style={{ background: "rgba(15, 25, 50, 0.6)", border: "1px solid rgba(77, 168, 240, 0.2)" }}>
                <p className="text-xs font-medium" style={{ color: "#6C757D" }}>PONTOS TOTAIS</p>
                <p className="text-2xl font-bold mt-1" style={{ color: "#54b4f7" }}>{metricas.totalPontos}</p>
                <p className="text-xs" style={{ color: "#6C757D" }}>{metricas.rodadasJogadas} rodada(s)</p>
              </div>
              {/* MEDIA/RODADA */}
              <div className="rounded-xl p-3 text-center" style={{ background: "rgba(15, 25, 50, 0.6)", border: "1px solid rgba(77, 168, 240, 0.2)" }}>
                <p className="text-xs font-medium" style={{ color: "#6C757D" }}>MEDIA/RODADA</p>
                <p className="text-2xl font-bold mt-1" style={{ color: "#FFD700" }}>{metricas.media}</p>
                <p className="text-xs" style={{ color: "#6C757D" }}>pts/rodada</p>
              </div>
              {/* PATRIMONIO */}
              <div className="rounded-xl p-3 text-center" style={{ background: "rgba(15, 25, 50, 0.6)", border: "1px solid rgba(77, 168, 240, 0.2)" }}>
                <p className="text-xs font-medium" style={{ color: "#6C757D" }}>PATRIMONIO</p>
                <p className="text-2xl font-bold mt-1" style={{ color: metricas.patrimonioVar >= 0 ? "#28a745" : "#dc3545" }}>
                  C$ {metricas.patrimonio}
                </p>
                <p className="text-xs" style={{ color: metricas.patrimonioVar >= 0 ? "#28a745" : "#dc3545" }}>
                  {metricas.patrimonioVar >= 0 ? "+" : ""}{metricas.patrimonioVar} vs inicial
                </p>
              </div>
              {/* MELHOR RODADA */}
              <div className="rounded-xl p-3 text-center" style={{ background: "rgba(15, 25, 50, 0.6)", border: "1px solid rgba(77, 168, 240, 0.2)" }}>
                <p className="text-xs font-medium" style={{ color: "#6C757D" }}>MELHOR RODADA</p>
                <p className="text-2xl font-bold mt-1" style={{ color: "#28a745" }}>{metricas.melhorPontos}</p>
                <p className="text-xs" style={{ color: "#6C757D" }}>R{metricas.melhorRodada}</p>
              </div>
            </div>
          )}

          {/* Performance Chart - Green/Red bars like Streamlit */}
          {metricas && metricas.chartData.length > 0 && (
            <div className="rounded-xl p-5" style={{ background: "rgba(15, 25, 50, 0.6)", border: "1px solid rgba(77, 168, 240, 0.2)" }}>
              <h3 className="text-base font-bold mb-4" style={{ color: "#f1f5f9" }}>
                Desempenho por Rodada
              </h3>
              <ResponsiveContainer width="100%" height={280}>
                <ComposedChart data={metricas.chartData}>
                  <XAxis dataKey="rodada" stroke="#6C757D" fontSize={12} axisLine={false} tickLine={false} />
                  <YAxis stroke="#6C757D" fontSize={12} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "rgba(15, 23, 42, 0.95)",
                      border: "1px solid rgba(77, 168, 240, 0.3)",
                      borderRadius: "8px",
                      color: "#f1f5f9",
                    }}
                    formatter={(value: number, name: string) => [
                      `${value.toFixed(1)} pts`,
                      name === "real" ? "Real" : "Previsto",
                    ]}
                  />
                  <Legend
                    formatter={(value: string) => (
                      <span style={{ color: "#f1f5f9", fontSize: "0.85em" }}>
                        {value === "real" ? "Real" : "Previsto"}
                      </span>
                    )}
                  />
                  {/* Média line */}
                  <ReferenceLine
                    y={metricas.media}
                    stroke="rgba(255,255,255,0.3)"
                    strokeDasharray="5 5"
                    label={{ value: `Média: ${metricas.media}`, fill: "rgba(255,255,255,0.5)", fontSize: 11, position: "right" }}
                  />
                  {/* Green/Red bars based on above/below average */}
                  <Bar dataKey="real" name="real" radius={[4, 4, 0, 0]}>
                    <LabelList dataKey="real" position="top" fill="#f1f5f9" fontSize={11} formatter={(v: number) => v > 0 ? Math.round(v) : ''} />
                    {metricas.chartData.map((entry: any, index: number) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.real >= metricas!.media ? "#28a745" : "#dc3545"}
                      />
                    ))}
                  </Bar>
                  {/* Previsto dotted line */}
                  <Line
                    dataKey="previsto"
                    name="previsto"
                    stroke="rgba(255, 215, 0, 0.6)"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    dot={{ r: 4, fill: "#FFD700" }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Mini Escalação */}
          <div className="rounded-xl p-5" style={{ background: "rgba(15, 25, 50, 0.6)", border: "1px solid rgba(77, 168, 240, 0.2)" }}>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-base font-bold flex items-center gap-2" style={{ color: "#54b4f7" }}>
                <img src={CAMISA_URL} alt="" className="h-5 w-5 object-contain" />
                Escalação Ativa
              </h3>
              <button onClick={() => setLocation("/escalacao")} className="text-xs font-medium" style={{ color: "#54b4f7" }}>
                Ver completa →
              </button>
            </div>
            {escalacaoAtual ? (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span style={{ color: "#6C757D" }}>
                    Formação: <strong style={{ color: "#54b4f7" }}>{escalacaoAtual.formacao}</strong>
                  </span>
                  <span style={{ color: "#FFD700", fontWeight: 700, fontSize: "0.85rem" }}>
                    {escalacaoAtual.pontuacao_esperada?.toFixed(1)} pts previsto
                  </span>
                </div>
                <div className="space-y-0.5">
                  {escalacaoAtual.titulares?.slice(0, 12).map((j: any) => {
                    const isCap = escalacaoAtual.capitao?.atleta_id === j.atleta_id;
                    return (
                      <div key={j.atleta_id} className="flex items-center gap-2 text-sm py-1 px-2 rounded" style={{ borderBottom: "1px solid rgba(77, 168, 240, 0.08)" }}>
                        <span className="text-xs font-semibold" style={{ color: "#6C757D", minWidth: 28 }}>
                          {j.posicao_abreviacao || "—"}
                        </span>
                        {isCap && <span style={{ color: "#FFD700", fontSize: "0.7rem", fontWeight: 800 }}>C</span>}
                        <ClubeBadge clubeId={j.clube_id} size={16} showName={false} />
                        <span className="truncate" style={{ color: "#f1f5f9", fontWeight: 600 }}>{j.apelido}</span>
                        <span className="ml-auto shrink-0" style={{ color: "#54b4f7", fontWeight: 600, fontSize: "0.8rem" }}>
                          C$ {j.preco?.toFixed(2)}
                        </span>
                        <span className="shrink-0" style={{ color: "#28a745", fontWeight: 700, fontSize: "0.8rem" }}>
                          {j.pontuacao_esperada?.toFixed(1)}p
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="text-center py-6">
                <img src={CAMISA_URL} alt="" className="h-12 w-12 mx-auto mb-2 opacity-30" />
                <p className="text-sm" style={{ color: "#6C757D" }}>Nenhuma escalação ativa</p>
                <button onClick={() => setLocation("/escalacao")} className="text-xs mt-2 px-3 py-1 rounded" style={{ color: "#54b4f7", border: "1px solid rgba(77, 168, 240, 0.3)" }}>
                  Escalar Time
                </button>
              </div>
            )}
          </div>

          {/* Jogos da Rodada - table format like Streamlit */}
          <div className="rounded-xl p-5" style={{ background: "rgba(15, 25, 50, 0.6)", border: "1px solid rgba(77, 168, 240, 0.2)" }}>
            <h3 className="text-base font-bold mb-4" style={{ color: "#54b4f7" }}>
              Jogos da Rodada
            </h3>
            {partidasAgrupadas.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full" style={{ borderCollapse: "collapse" }}>
                  <tbody>
                    {partidasAgrupadas.map((grupo, gi) => (
                      <>
                        <tr key={`g-${gi}`}>
                          <td colSpan={4} className="py-2 px-1 text-xs font-bold" style={{ color: "#54b4f7", borderBottom: "1px solid rgba(77, 168, 240, 0.2)" }}>
                            {grupo.label}
                          </td>
                        </tr>
                        {grupo.jogos.map((p: any, pi: number) => {
                          const valida = p.valida !== false;
                          const placar = p.placar_oficial_mandante != null
                            ? `${p.placar_oficial_mandante} x ${p.placar_oficial_visitante}`
                            : "vs";
                          return (
                            <tr key={`j-${gi}-${pi}`} style={{ background: pi % 2 === 0 ? "#0b1d33" : "#111d33" }}>
                              <td className="py-1.5 px-1 text-right text-sm font-bold" style={{
                                color: valida ? "white" : "#666",
                                textDecoration: valida ? "none" : "line-through",
                                width: "35%"
                              }}>
                                <div className="flex items-center justify-end gap-1.5">
                                  {p.mandante}
                                  <ClubeBadge clubeId={p.clube_casa_id} size={16} showName={false} />
                                </div>
                              </td>
                              <td className="py-1.5 px-1 text-center text-sm" style={{ color: "#6C757D", width: "12%" }}>
                                {placar}
                              </td>
                              <td className="py-1.5 px-1 text-left text-sm font-bold" style={{
                                color: valida ? "white" : "#666",
                                textDecoration: valida ? "none" : "line-through",
                                width: "35%"
                              }}>
                                <div className="flex items-center gap-1.5">
                                  <ClubeBadge clubeId={p.clube_visitante_id} size={16} showName={false} />
                                  {p.visitante}
                                </div>
                              </td>
                              <td className="py-1.5 px-1 text-center" style={{ width: "18%" }}>
                                {!valida && (
                                  <span className="text-[10px] font-bold" style={{ color: "#ff6b6b" }}>(Não vale)</span>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </>
                    ))}
                  </tbody>
                </table>
                {nValidos < nTotal && (
                  <p className="text-xs mt-2" style={{ color: "#6C757D" }}>
                    {nValidos} de {nTotal} jogos valem para o Cartola. Jogos riscados não pontuam.
                  </p>
                )}
              </div>
            ) : (
              <p className="text-sm text-center py-4" style={{ color: "#6C757D" }}>Jogos da rodada indisponíveis no momento</p>
            )}
          </div>
        </>
      )}
    </div>
  );
}
