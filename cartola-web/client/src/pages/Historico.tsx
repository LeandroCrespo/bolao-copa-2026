import { trpc } from "@/lib/trpc";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2 } from "lucide-react";
import { useMemo, useState } from "react";
import {
  ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, ReferenceLine, Cell,
} from "recharts";
import { ClubeBadge } from "@/components/ClubeBadge";

const POSICOES: Record<number, string> = { 1: "GOL", 2: "LAT", 3: "ZAG", 4: "MEI", 5: "ATA", 6: "TEC" };
const POS_COLORS: Record<string, string> = {
  GOL: "#FFC107", LAT: "#54b4f7", ZAG: "#34d399", MEI: "#a78bfa", ATA: "#f87171", TEC: "#94a3b8",
};

export default function Historico() {
  const { data: rodadas } = trpc.db.rodadasProcessadas.useQuery();
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const anos = useMemo(() => {
    if (!rodadas) return [2026, 2025];
    const set = new Set(rodadas.map((r: any) => r.ano));
    return Array.from(set).sort((a, b) => b - a);
  }, [rodadas]);

  const [selectedAno, setSelectedAno] = useState<number | null>(null);
  const ano = selectedAno || anos[0] || 2026;

  const { data: escalacoes, isLoading } = trpc.db.historicoRodadas.useQuery({ ano });
  const rows = (escalacoes || []) as any[];

  const parsedRows = useMemo(() => {
    return rows.map((row: any) => {
      const esc = typeof row.escalacao_json === "string" ? JSON.parse(row.escalacao_json) : row.escalacao_json;
      return { ...row, esc };
    });
  }, [rows]);

  const chartData = useMemo(() => {
    return [...parsedRows]
      .sort((a, b) => a.rodada - b.rodada)
      .map((e) => {
        const real = e.pontos_reais != null ? Number(e.pontos_reais) : null;
        return {
          rodada: `R${e.rodada}`,
          previsto: e.esc?.pontuacao_prevista || 0,
          real,
        };
      });
  }, [parsedRows]);

  const totais = useMemo(() => {
    const processadas = parsedRows.filter((e) => e.pontos_reais != null && Number(e.pontos_reais) > 0);
    const totalPrevisto = processadas.reduce((s, e) => s + (e.esc?.pontuacao_prevista || 0), 0);
    const totalReal = processadas.reduce((s, e) => s + Number(e.pontos_reais || 0), 0);
    const melhor = processadas.length > 0 ? Math.max(...processadas.map((e) => Number(e.pontos_reais) || 0)) : 0;
    const pior = processadas.length > 0 ? Math.min(...processadas.map((e) => Number(e.pontos_reais) || 0)) : 0;
    const media = processadas.length > 0 ? totalReal / processadas.length : 0;
    const aproveitamento = totalPrevisto > 0 ? (totalReal / totalPrevisto) * 100 : 0;
    return { totalPrevisto, totalReal, melhor, pior, media, rodadas: processadas.length, aproveitamento };
  }, [parsedRows]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "#f1f5f9" }}>📋 Histórico de Escalações</h1>
          <p className="text-sm mt-1" style={{ color: "#94a3b8" }}>
            Escalações salvas, pontuação real vs prevista e evolução
          </p>
        </div>
        <Select value={String(ano)} onValueChange={(v) => setSelectedAno(Number(v))}>
          <SelectTrigger className="w-[120px]" style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(148, 163, 184, 0.2)", color: "#f1f5f9" }}>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {anos.map((a) => <SelectItem key={a} value={String(a)}>{a}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center min-h-[40vh]">
          <Loader2 className="h-8 w-8 animate-spin" style={{ color: "#54b4f7" }} />
        </div>
      ) : parsedRows.length === 0 ? (
        <div className="rounded-xl p-12 text-center" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
          <p style={{ color: "#94a3b8" }}>Nenhuma escalação salva para {ano}.</p>
        </div>
      ) : (
        <>
          {/* Summary Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
            <StatBox label="Rodadas" value={String(totais.rodadas)} color="#f1f5f9" />
            <StatBox label="Total Real" value={totais.totalReal.toFixed(1)} color="#54b4f7" />
            <StatBox label="Média" value={totais.media.toFixed(1)} color="#f1f5f9" />
            <StatBox label="Melhor" value={totais.melhor.toFixed(1)} color="#34d399" />
            <StatBox label="Pior" value={totais.pior.toFixed(1)} color="#f87171" />
            <StatBox label="Total Previsto" value={totais.totalPrevisto.toFixed(1)} color="#FFC107" />
            <StatBox label="Aproveitamento" value={`${totais.aproveitamento.toFixed(0)}%`}
              color={totais.aproveitamento >= 100 ? "#34d399" : "#FFC107"} />
          </div>

          {/* Evolution Chart - Streamlit style */}
          {chartData.length > 1 && (
            <div className="rounded-xl p-4" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
              <p className="font-bold mb-3" style={{ color: "#f1f5f9" }}>📊 Desempenho por Rodada</p>
              <ResponsiveContainer width="100%" height={350}>
                <ComposedChart data={chartData} margin={{ top: 10, right: 20, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
                  <XAxis dataKey="rodada" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#1e293b", border: "1px solid rgba(148, 163, 184, 0.2)", borderRadius: "8px", color: "#f1f5f9" }}
                    formatter={(value: any, name: string) => [
                      value != null ? Number(value).toFixed(1) : "—",
                      name === "real" ? "Real" : "Previsto",
                    ]}
                  />
                  <Legend wrapperStyle={{ color: "#94a3b8" }} />
                  <ReferenceLine y={totais.media} stroke="#34d399" strokeDasharray="5 5"
                    label={{ value: `Média ${totais.media.toFixed(1)}`, fill: "#34d399", fontSize: 10, position: "right" }} />
                  <Bar dataKey="real" name="Real" radius={[4, 4, 0, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell key={index}
                        fill={entry.real != null && entry.real >= (totais.media || 0) ? "#28A745" : "#DC3545"} />
                    ))}
                  </Bar>
                  <Line dataKey="previsto" name="Previsto" stroke="#FFC107" strokeWidth={2.5}
                    dot={{ r: 3, fill: "#FFC107" }} strokeDasharray="5 5" />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Rounds List */}
          <div className="space-y-2">
            {[...parsedRows].sort((a, b) => b.rodada - a.rodada).map((e) => {
              const isExpanded = expandedId === e.id;
              const esc = e.esc;
              const pontosReais = e.pontos_reais != null ? Number(e.pontos_reais) : null;
              const pontosPrev = esc?.pontuacao_prevista || 0;
              const diff = pontosReais != null ? pontosReais - pontosPrev : null;
              const formacao = e.formacao || esc?.formacao || "?";
              const capitao = esc?.capitao;
              const capitaoId = esc?.capitao_id || (capitao ? String(capitao.atleta_id) : null);
              const jogadores = esc?.jogadores || [];
              const reservas = esc?.reservas || {};
              const reservaLuxo = esc?.reserva_luxo;
              const substituicoes = esc?.substituicoes || [];
              const orcDisp = esc?.orcamento_disponivel || 100;
              const processado = esc?.processado === true || (pontosReais != null && pontosReais > 0);

              // Group jogadores by position
              const jogadoresByPos: Record<number, any[]> = {};
              for (const j of jogadores) {
                const posId = j.pos_id || j.posicao_id || 0;
                if (!jogadoresByPos[posId]) jogadoresByPos[posId] = [];
                jogadoresByPos[posId].push(j);
              }

              // Calculate valorização
              let valorizacao = 0;
              for (const j of jogadores) {
                valorizacao += (j.variacao || 0);
              }

              return (
                <div key={e.id} className="rounded-xl overflow-hidden transition-all"
                  style={{
                    background: "rgba(15, 23, 42, 0.6)",
                    border: isExpanded ? "1px solid rgba(84, 180, 247, 0.3)" : "1px solid rgba(148, 163, 184, 0.1)",
                  }}>
                  {/* Collapsed Header */}
                  <button className="w-full text-left p-4 transition-colors"
                    onClick={() => setExpandedId(isExpanded ? null : e.id)}
                    onMouseEnter={(ev) => ev.currentTarget.style.background = "rgba(84, 180, 247, 0.03)"}
                    onMouseLeave={(ev) => ev.currentTarget.style.background = "transparent"}>
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <div className="rounded-lg p-2 text-center min-w-[55px]" style={{ background: "rgba(84, 180, 247, 0.1)" }}>
                          <p className="text-[10px]" style={{ color: "#64748b" }}>Rodada</p>
                          <p className="text-lg font-bold" style={{ color: "#54b4f7" }}>{e.rodada}</p>
                        </div>
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-xs font-bold px-2 py-0.5 rounded" style={{ background: "rgba(148, 163, 184, 0.1)", color: "#94a3b8" }}>{formacao}</span>
                            {processado && <span className="text-[10px] font-bold px-2 py-0.5 rounded" style={{ background: "rgba(52, 211, 153, 0.15)", color: "#34d399" }}>✅ Processada</span>}
                            {!processado && <span className="text-[10px] font-bold px-2 py-0.5 rounded" style={{ background: "rgba(234, 179, 8, 0.15)", color: "#EAB308" }}>⏳ Aguardando</span>}
                            {capitao && <span className="text-xs" style={{ color: "#94a3b8" }}>Cap: <strong style={{ color: "#EAB308" }}>{capitao.apelido}</strong></span>}
                          </div>
                          <p className="text-xs mt-0.5" style={{ color: "#64748b" }}>
                            Orçamento: C$ {Number(orcDisp).toFixed(2)}
                            {processado && valorizacao !== 0 && (
                              <span style={{ color: valorizacao >= 0 ? "#34d399" : "#f87171" }}>
                                {" "}| Val: {valorizacao >= 0 ? "+" : ""}{valorizacao.toFixed(2)}
                              </span>
                            )}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="text-lg font-bold" style={{ color: processado ? "#54b4f7" : "#64748b" }}>
                            {processado && pontosReais != null ? pontosReais.toFixed(1) : "—"}
                          </p>
                          <p className="text-[10px]" style={{ color: "#64748b" }}>Real</p>
                        </div>
                        <div className="text-right">
                          <p className="text-lg font-bold" style={{ color: "#FFC107" }}>{pontosPrev.toFixed(1)}</p>
                          <p className="text-[10px]" style={{ color: "#64748b" }}>Previsto</p>
                        </div>
                        {diff != null && processado && (
                          <div className="text-right min-w-[45px]">
                            <p className="text-sm font-bold" style={{ color: diff >= 0 ? "#34d399" : "#f87171" }}>
                              {diff >= 0 ? "+" : ""}{diff.toFixed(1)}
                            </p>
                          </div>
                        )}
                        <span style={{ color: "#64748b" }}>{isExpanded ? "▲" : "▼"}</span>
                      </div>
                    </div>
                  </button>

                  {/* Expanded Detail */}
                  {isExpanded && (
                    <div className="px-4 pb-4" style={{ borderTop: "1px solid rgba(148, 163, 184, 0.1)" }}>
                      {/* Metrics row */}
                      <div className="grid grid-cols-3 sm:grid-cols-5 gap-3 mt-3">
                        <MiniStat label="Pts Real" value={processado && pontosReais != null ? pontosReais.toFixed(1) : "—"} color="#54b4f7" />
                        <MiniStat label="Pts Previsto" value={pontosPrev.toFixed(1)} color="#FFC107" />
                        <MiniStat label="Orçamento" value={`C$ ${Number(orcDisp).toFixed(1)}`} color="#34d399" />
                        {processado && <MiniStat label="Valorização" value={`${valorizacao >= 0 ? "+" : ""}${valorizacao.toFixed(2)}`} color={valorizacao >= 0 ? "#34d399" : "#f87171"} />}
                        {processado && diff != null && <MiniStat label="Diferença" value={`${diff >= 0 ? "+" : ""}${diff.toFixed(1)}`} color={diff >= 0 ? "#34d399" : "#f87171"} />}
                      </div>

                      {/* Substituições alerts */}
                      {substituicoes.length > 0 && (
                        <div className="mt-3 space-y-1">
                          {substituicoes.map((sub: any, i: number) => (
                            <div key={i} className="rounded-lg px-3 py-2 text-xs flex items-center gap-2"
                              style={{ background: "rgba(52, 211, 153, 0.08)", border: "1px solid rgba(52, 211, 153, 0.2)" }}>
                              <span>🔄</span>
                              <span style={{ color: "#34d399" }}>Reserva entrou!</span>
                              <span style={{ color: "#f1f5f9" }}>{sub.entrou?.apelido || sub.entrou}</span>
                              <span style={{ color: "#64748b" }}>substituiu</span>
                              <span style={{ color: "#f87171" }}>{sub.saiu?.apelido || sub.saiu}</span>
                              {sub.ganho != null && (
                                <span className="ml-auto font-bold" style={{ color: "#34d399" }}>
                                  {Number(sub.ganho).toFixed(2)} pts
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Players by Position */}
                      {jogadores.length > 0 && (
                        <div className="mt-4 space-y-3">
                          {[1, 3, 2, 4, 5, 6].map((posId) => {
                            const posJogadores = jogadoresByPos[posId];
                            if (!posJogadores || posJogadores.length === 0) return null;
                            const posNome = POSICOES[posId] || "?";
                            const posColor = POS_COLORS[posNome] || "#94a3b8";
                            return (
                              <div key={posId}>
                                <div className="flex items-center gap-2 mb-1.5">
                                  <span className="text-[10px] font-bold px-2 py-0.5 rounded" style={{ background: `${posColor}20`, color: posColor }}>{posNome}</span>
                                </div>
                                <div className="space-y-1">
                                  {posJogadores.map((j: any) => {
                                    const isCapitao = j.e_capitao || (capitaoId && String(j.atleta_id) === String(capitaoId));
                                    const ptsReal = j.pontos_real ?? j.pontos_reais;
                                    const scorePrev = j.score_previsto ?? j.pontuacao_esperada ?? j.score ?? 0;
                                    const confronto = j.confronto || "";
                                    const explicacao = j.explicacao || {};
                                    const scout = j.scout || {};
                                    const scoutEntries = Object.entries(scout).filter(([, v]) => v !== 0 && v != null);

                                    return (
                                      <div key={j.atleta_id} className="rounded-lg px-3 py-2"
                                        style={{ background: "rgba(30, 41, 59, 0.4)", border: "1px solid rgba(148, 163, 184, 0.06)" }}>
                                        <div className="flex items-center justify-between gap-2">
                                          <div className="flex items-center gap-2">
                                            {j.clube_id && <ClubeBadge clubeId={j.clube_id} size={18} />}
                                            <span className="font-bold text-sm" style={{ color: "#f1f5f9" }}>
                                              {j.apelido}
                                              {isCapitao && <span className="ml-1 text-[9px] font-bold px-1 py-0.5 rounded" style={{ background: "rgba(234, 179, 8, 0.2)", color: "#EAB308" }}>C</span>}
                                            </span>
                                            {j.clube && <span className="text-[10px]" style={{ color: "#64748b" }}>{j.clube}</span>}
                                            {confronto && <span className="text-[10px]" style={{ color: "#94a3b8" }}>vs {confronto}</span>}
                                          </div>
                                          <div className="flex items-center gap-3 text-xs">
                                            <span style={{ color: "#4da8f0" }}>C$ {(j.preco || 0).toFixed(2)}</span>
                                            <span style={{ color: "#FFC107" }}>Prev: {Number(scorePrev).toFixed(1)}</span>
                                            {processado && ptsReal != null && (
                                              <span className="font-bold" style={{ color: ptsReal >= 0 ? "#34d399" : "#f87171" }}>
                                                Real: {Number(ptsReal).toFixed(1)}
                                                {isCapitao && <span className="text-[9px] ml-0.5" style={{ color: "#EAB308" }}>(×1.5)</span>}
                                              </span>
                                            )}
                                          </div>
                                        </div>

                                        {/* Explicação */}
                                        {explicacao.motivo && (
                                          <p className="text-[10px] mt-1" style={{ color: "#94a3b8" }}>
                                            💡 {explicacao.motivo}
                                            {explicacao.detalhes && <span> — {typeof explicacao.detalhes === 'string' ? explicacao.detalhes : JSON.stringify(explicacao.detalhes)}</span>}
                                          </p>
                                        )}

                                        {/* Scouts */}
                                        {processado && scoutEntries.length > 0 && (
                                          <div className="flex flex-wrap gap-1 mt-1">
                                            {scoutEntries.map(([key, val]) => (
                                              <span key={key} className="text-[9px] px-1 py-0.5 rounded"
                                                style={{
                                                  background: Number(val) > 0 ? "rgba(52, 211, 153, 0.1)" : "rgba(248, 113, 113, 0.1)",
                                                  color: Number(val) > 0 ? "#34d399" : "#f87171",
                                                }}>
                                                {key}: {String(val)}
                                              </span>
                                            ))}
                                          </div>
                                        )}
                                      </div>
                                    );
                                  })}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}

                      {/* Reservas */}
                      {(Object.keys(reservas).length > 0 || reservaLuxo) && (
                        <div className="mt-4">
                          <p className="text-xs font-bold uppercase tracking-wider mb-2" style={{ color: "#94a3b8" }}>🔄 Reservas</p>
                          <div className="space-y-1">
                            {Object.entries(reservas).map(([pos, r]: [string, any]) => r && (
                              <div key={pos} className="rounded-lg px-3 py-2 flex items-center justify-between"
                                style={{ background: "rgba(30, 41, 59, 0.3)", border: "1px solid rgba(148, 163, 184, 0.06)" }}>
                                <div className="flex items-center gap-2">
                                  <span className="text-[9px] font-bold px-1.5 py-0.5 rounded" style={{ background: "rgba(148, 163, 184, 0.1)", color: "#94a3b8" }}>
                                    {r.posicao || POSICOES[r.pos_id] || pos}
                                  </span>
                                  {r.clube_id && <ClubeBadge clubeId={r.clube_id} size={16} />}
                                  <span className="text-sm" style={{ color: "#f1f5f9" }}>{r.apelido}</span>
                                </div>
                                <div className="flex items-center gap-3 text-xs">
                                  <span style={{ color: "#4da8f0" }}>C$ {(r.preco || 0).toFixed(2)}</span>
                                  {r.pontos_real != null && (
                                    <span className="font-bold" style={{ color: r.pontos_real >= 0 ? "#34d399" : "#f87171" }}>
                                      {Number(r.pontos_real).toFixed(1)} pts
                                    </span>
                                  )}
                                </div>
                              </div>
                            ))}
                            {reservaLuxo && (
                              <div className="rounded-lg px-3 py-2 flex items-center justify-between"
                                style={{ background: "rgba(234, 179, 8, 0.05)", border: "1px solid rgba(234, 179, 8, 0.2)" }}>
                                <div className="flex items-center gap-2">
                                  <span className="text-[9px] font-bold px-1.5 py-0.5 rounded" style={{ background: "rgba(234, 179, 8, 0.15)", color: "#EAB308" }}>⭐ LUXO</span>
                                  {reservaLuxo.clube_id && <ClubeBadge clubeId={reservaLuxo.clube_id} size={16} />}
                                  <span className="text-sm font-bold" style={{ color: "#f1f5f9" }}>{reservaLuxo.apelido}</span>
                                  <span className="text-[10px]" style={{ color: "#64748b" }}>{POSICOES[reservaLuxo.pos_id] || ""}</span>
                                </div>
                                <div className="flex items-center gap-3 text-xs">
                                  <span style={{ color: "#4da8f0" }}>C$ {(reservaLuxo.preco || 0).toFixed(2)}</span>
                                  <span style={{ color: "#FFC107" }}>Prev: {Number(reservaLuxo.score_previsto || reservaLuxo.media || 0).toFixed(1)}</span>
                                  {reservaLuxo.pontos_real != null && (
                                    <span className="font-bold" style={{ color: reservaLuxo.pontos_real >= 0 ? "#34d399" : "#f87171" }}>
                                      {Number(reservaLuxo.pontos_real).toFixed(1)} pts
                                    </span>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Acurácia */}
                      {esc?.acuracia && (
                        <div className="mt-4 rounded-lg p-3" style={{ background: "rgba(30, 41, 59, 0.3)", border: "1px solid rgba(148, 163, 184, 0.08)" }}>
                          <p className="text-xs font-bold uppercase tracking-wider mb-1" style={{ color: "#94a3b8" }}>📊 Acurácia</p>
                          <div className="flex flex-wrap gap-4 text-xs" style={{ color: "#cbd5e1" }}>
                            {esc.acuracia.acertos_titulares != null && (
                              <span>Acertos Titulares: <strong style={{ color: "#54b4f7" }}>{esc.acuracia.acertos_titulares}/12</strong></span>
                            )}
                            {esc.acuracia.capitao_correto != null && (
                              <span>Capitão: <strong style={{ color: esc.acuracia.capitao_correto ? "#34d399" : "#f87171" }}>{esc.acuracia.capitao_correto ? "Acertou" : "Errou"}</strong></span>
                            )}
                            {esc.acuracia.aproveitamento != null && (
                              <span>Aproveitamento: <strong style={{ color: "#FFC107" }}>{esc.acuracia.aproveitamento}%</strong></span>
                            )}
                          </div>
                        </div>
                      )}

                      <p className="text-[10px] mt-3" style={{ color: "#475569" }}>
                        Salvo em: {e.data_criacao ? new Date(e.data_criacao).toLocaleString("pt-BR") : "—"}
                      </p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

function StatBox({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="rounded-xl p-3 text-center" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.1)" }}>
      <p className="text-[10px] uppercase" style={{ color: "#64748b" }}>{label}</p>
      <p className="text-xl font-bold mt-0.5" style={{ color }}>{value}</p>
    </div>
  );
}

function MiniStat({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="rounded-lg p-2 text-center" style={{ background: "rgba(30, 41, 59, 0.4)", border: "1px solid rgba(148, 163, 184, 0.08)" }}>
      <p className="text-[9px] uppercase" style={{ color: "#64748b" }}>{label}</p>
      <p className="text-sm font-bold" style={{ color }}>{value}</p>
    </div>
  );
}
