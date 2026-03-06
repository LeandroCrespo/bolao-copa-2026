import { useState, useMemo } from "react";
import { trpc } from "@/lib/trpc";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Loader2 } from "lucide-react";
import { useLocation } from "wouter";
import { ClubeBadge } from "@/components/ClubeBadge";
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine, Area, ComposedChart, PieChart, Pie, Cell, LabelList
} from "recharts";

const POS_COLORS: Record<string, string> = {
  GOL: '#f59e0b', LAT: '#3b82f6', ZAG: '#10b981', MEI: '#ef4444', ATA: '#8b5cf6', TEC: '#ec4899'
};
const JUSTIFICATIVA_COLORS: Record<string, string> = {
  'Boa Fase': '#22c55e', 'Consistente': '#3b82f6', 'Recuperação': '#f59e0b',
  'Premium': '#8b5cf6', 'Custo-Benefício': '#06b6d4', 'Aposta': '#ef4444', 'Em Queda': '#6b7280'
};
const MEDAL = ['\u{1F947}', '\u{1F948}', '\u{1F949}', '4\u00B0', '5\u00B0'];
const POSICOES: Record<number, string> = { 1: "GOL", 2: "LAT", 3: "ZAG", 4: "MEI", 5: "ATA", 6: "TEC" };
const FORMACOES = ["4-3-3", "4-4-2", "3-5-2", "4-5-1", "3-4-3", "5-3-2", "5-4-1"];

export default function Simulacao() {
  const { data: rodadas } = trpc.db.rodadasProcessadas.useQuery();
  const [, setLocation] = useLocation();

  const anos = useMemo(() => {
    if (!rodadas) return [];
    const set = new Set(rodadas.map((r: any) => r.ano));
    return Array.from(set).sort((a: number, b: number) => b - a);
  }, [rodadas]);

  const [selectedAno, setSelectedAno] = useState<number | null>(null);
  const [selectedRodada, setSelectedRodada] = useState<number | null>(null);
  const [formacao, setFormacao] = useState("4-3-3");
  const [orcamento, setOrcamento] = useState(100);
  const [formacaoAutomatica, setFormacaoAutomatica] = useState(true);
  const [orcDinamico, setOrcDinamico] = useState(true);
  const [tab, setTab] = useState("todas");
  const [expandedRodada, setExpandedRodada] = useState<number | null>(null);

  const ano = selectedAno || anos[0] || 2026;
  const rodadasDoAno = useMemo(() => {
    return rodadas?.filter((r: any) => r.ano === ano).sort((a: any, b: any) => b.rodada - a.rodada) || [];
  }, [rodadas, ano]);
  const rodada = selectedRodada || rodadasDoAno[0]?.rodada;

  const { data: jogadores } = trpc.db.jogadoresRodada.useQuery(
    { rodada: rodada!, ano },
    { enabled: !!rodada && tab === "rodada" }
  );

  const simularRodada = trpc.estrategia.simularRodada.useMutation();
  const simularTodas = trpc.estrategia.simularTodasRodadas.useMutation();

  const data = simularTodas.data;
  const resultados = data?.resultados || [];

  // Chart data
  const chartEvolucao = useMemo(() => resultados.map((r: any) => ({
    name: `R${r.rodada}`,
    Escalado: r.pontos_reais,
    'Previsão': r.pts_previsto,
    Ideal: r.pts_ideal,
  })), [resultados]);

  const chartAprov = useMemo(() => resultados.map((r: any) => ({
    name: `R${r.rodada}`,
    'Por Rodada': r.aproveitamento,
    Acumulado: r.aproveitamento_acumulado,
  })), [resultados]);

  const chartPosicao = useMemo(() => {
    if (!data?.aprovPosicao) return [];
    return Object.entries(data.aprovPosicao).map(([pos, val]) => ({
      name: pos, Aproveitamento: val as number,
    }));
  }, [data]);

  const chartJustificativas = useMemo(() => {
    if (!data?.justificativas) return [];
    return Object.entries(data.justificativas).map(([name, value]) => ({
      name, value: value as number,
    }));
  }, [data]);

  const chartFormacoes = useMemo(() => {
    if (!data?.formacoes) return [];
    return Object.entries(data.formacoes)
      .sort((a, b) => (b[1] as number) - (a[1] as number))
      .map(([name, value]) => ({ name, value: value as number }));
  }, [data]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2" style={{ color: "#f1f5f9" }}>
          <span>🔬</span> Simulação Histórica
        </h1>
        <p className="text-sm mt-1" style={{ color: "#94a3b8" }}>
          Simula a escalação automática em rodadas passadas e compara com o time ideal
        </p>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="grid w-full grid-cols-2" style={{ background: "rgba(15, 23, 42, 0.6)" }}>
          <TabsTrigger value="todas">Todas as Rodadas</TabsTrigger>
          <TabsTrigger value="rodada">Rodada Individual</TabsTrigger>
        </TabsList>

        {/* ===== ALL ROUNDS TAB ===== */}
        <TabsContent value="todas" className="space-y-4">
          {/* Controls */}
          <div className="rounded-xl p-4" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 items-end">
              <div>
                <Label className="text-xs" style={{ color: "#94a3b8" }}>Ano</Label>
                <Select value={String(ano)} onValueChange={v => { setSelectedAno(Number(v)); }}>
                  <SelectTrigger style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(148, 163, 184, 0.2)", color: "#f1f5f9" }}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {anos.map(a => <SelectItem key={a} value={String(a)}>{a}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-xs" style={{ color: "#94a3b8" }}>Formação</Label>
                <Select value={formacaoAutomatica ? "auto" : formacao} onValueChange={v => {
                  if (v === 'auto') { setFormacaoAutomatica(true); } else { setFormacaoAutomatica(false); setFormacao(v); }
                }}>
                  <SelectTrigger style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(148, 163, 184, 0.2)", color: "#f1f5f9" }}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">Automático</SelectItem>
                    {FORMACOES.map(f => <SelectItem key={f} value={f}>{f}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-xs" style={{ color: "#94a3b8" }}>Orçamento (C$)</Label>
                <Input type="number" value={orcamento} onChange={e => setOrcamento(Number(e.target.value))}
                  style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(148, 163, 184, 0.2)", color: "#f1f5f9" }} />
              </div>
              <div className="flex items-center gap-2 pt-4">
                <Switch checked={orcDinamico} onCheckedChange={setOrcDinamico} />
                <Label className="text-xs" style={{ color: "#cbd5e1" }}>Orç. Dinâmico</Label>
              </div>
              <Button
                onClick={() => simularTodas.mutate({
                  ano,
                  formacao: formacaoAutomatica ? '4-3-3' : formacao,
                  orcamento,
                  formacaoAutomatica,
                  orcamentoDinamico: orcDinamico,
                })}
                disabled={simularTodas.isPending}
                style={{ background: "#22c55e", color: "#000", fontWeight: 700 }}
              >
                {simularTodas.isPending ? <><Loader2 className="h-4 w-4 animate-spin mr-2" /> Simulando...</> : '🚀 Simular'}
              </Button>
            </div>
          </div>

          {simularTodas.isPending && (
            <div className="rounded-xl p-12 text-center" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
              <div className="animate-spin text-4xl mb-4">⚽</div>
              <p className="text-lg font-semibold" style={{ color: "#f1f5f9" }}>Simulando todas as rodadas...</p>
              <p className="text-sm" style={{ color: "#94a3b8" }}>Isso pode levar alguns minutos</p>
            </div>
          )}

          {simularTodas.error && (
            <div className="rounded-xl p-4" style={{ background: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.3)" }}>
              <p style={{ color: "#f87171" }}>Erro: {simularTodas.error.message}</p>
            </div>
          )}

          {data && resultados.length > 0 && (
            <>
              {/* Summary Metrics */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                <MetricCard label="Total Pontos" value={data.total_pontos_reais.toFixed(1)} sub={`${data.total_rodadas} rodadas`} color="#34d399" />
                <MetricCard label="Média/Rodada" value={data.media_pontos_reais.toFixed(1)} sub="pts/rodada" color="#54b4f7" />
                <MetricCard label="Pts Ideal" value={data.total_pontos_ideal.toFixed(1)} sub="máximo possível" color="#eab308" />
                <MetricCard label="Aproveitamento" value={`${data.aproveitamento_total.toFixed(1)}%`} sub="vs ideal" color="#06b6d4" />
                <MetricCard label="Capitães OK" value={`${data.capitaes_ok}/${data.total_rodadas}`} sub={`${(data.capitaes_ok / data.total_rodadas * 100).toFixed(0)}% acerto`} color="#a78bfa" />
              </div>

              {/* Chart 1: Evolução por Rodada */}
              <div className="rounded-xl p-4" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
                <h3 className="font-bold mb-3" style={{ color: "#f1f5f9" }}>📈 Evolução por Rodada</h3>
                <ResponsiveContainer width="100%" height={350}>
                  <ComposedChart data={chartEvolucao}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} />
                    <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
                    <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: 8, color: '#f1f5f9' }} />
                    <Legend />
                    <ReferenceLine y={90} stroke="#ef4444" strokeDasharray="5 5" label={{ value: "Meta 90", fill: '#ef4444', fontSize: 10 }} />
                    <Area type="monotone" dataKey="Escalado" fill="rgba(59, 130, 246, 0.3)" stroke="#3b82f6" strokeWidth={2} />
                    <Line type="monotone" dataKey="Previsão" stroke="#22c55e" strokeDasharray="5 5" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="Ideal" stroke="#f59e0b" strokeDasharray="3 3" strokeWidth={2} dot={false} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>

              {/* Chart 2: Aproveitamento */}
              <div className="rounded-xl p-4" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
                <h3 className="font-bold mb-3" style={{ color: "#f1f5f9" }}>📊 Aproveitamento</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <ComposedChart data={chartAprov}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} />
                    <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} domain={[0, 100]} />
                    <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: 8, color: '#f1f5f9' }} formatter={(v: any) => `${Number(v).toFixed(1)}%`} />
                    <Legend />
                    <ReferenceLine y={50} stroke="#ef4444" strokeDasharray="5 5" label={{ value: "Meta 50%", fill: '#ef4444', fontSize: 10 }} />
                    <Bar dataKey="Por Rodada" fill="rgba(59, 130, 246, 0.5)" />
                    <Line type="monotone" dataKey="Acumulado" stroke="#22c55e" strokeWidth={2} dot={false} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>

              {/* Charts Row: Position + Justificativas */}
              <div className="grid md:grid-cols-2 gap-4">
                {/* Aproveitamento por Posição */}
                <div className="rounded-xl p-4" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
                  <h3 className="font-bold mb-3" style={{ color: "#f1f5f9" }}>🎯 Aproveitamento por Posição</h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={chartPosicao}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} />
                      <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} domain={[0, 100]} />
                      <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: 8, color: '#f1f5f9' }} formatter={(v: any) => `${Number(v).toFixed(1)}%`} />
                      <Bar dataKey="Aproveitamento">
                        {chartPosicao.map((entry, i) => (
                          <Cell key={i} fill={POS_COLORS[entry.name] || '#6b7280'} />
                        ))}
                        <LabelList dataKey="Aproveitamento" position="top" fill="#e5e7eb" fontSize={11} formatter={(v: any) => `${Number(v).toFixed(0)}%`} />
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Distribuição de Justificativas */}
                <div className="rounded-xl p-4" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
                  <h3 className="font-bold mb-3" style={{ color: "#f1f5f9" }}>🧠 Distribuição de Justificativas</h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <PieChart>
                      <Pie data={chartJustificativas} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, percent }: any) => `${name} ${(percent * 100).toFixed(0)}%`}>
                        {chartJustificativas.map((entry, i) => (
                          <Cell key={i} fill={JUSTIFICATIVA_COLORS[entry.name] || '#6b7280'} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: 8, color: '#f1f5f9' }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Gauges: Aproveitamento por Justificativa */}
              {data.justGauges && Object.keys(data.justGauges).length > 0 && (
                <div className="rounded-xl p-4" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
                  <h3 className="font-bold mb-3" style={{ color: "#f1f5f9" }}>📊 Aproveitamento por Justificativa</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {Object.entries(data.justGauges as Record<string, { acertos: number; total: number }>).map(([name, stats]) => {
                      const pct = stats.total > 0 ? (stats.acertos / stats.total * 100) : 0;
                      const barColor = pct >= 60 ? '#22c55e' : pct >= 40 ? '#eab308' : '#ef4444';
                      const textColor = pct >= 60 ? '#34d399' : pct >= 40 ? '#eab308' : '#f87171';
                      return (
                        <div key={name} className="text-center p-3 rounded-lg" style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(148, 163, 184, 0.1)" }}>
                          <div className="text-2xl font-bold" style={{ color: textColor }}>{pct.toFixed(0)}%</div>
                          <div className="text-xs mt-1" style={{ color: "#94a3b8" }}>{name}</div>
                          <div className="text-xs" style={{ color: "#64748b" }}>{stats.acertos}/{stats.total} acima da média</div>
                          <div className="mt-2 h-2 rounded-full overflow-hidden" style={{ background: "#374151" }}>
                            <div className="h-full rounded-full transition-all" style={{ width: `${Math.min(pct, 100)}%`, backgroundColor: barColor }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Formações + Top 5 */}
              <div className="grid md:grid-cols-2 gap-4">
                {/* Formações Mais Escaladas */}
                <div className="rounded-xl p-4" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
                  <h3 className="font-bold mb-3" style={{ color: "#f1f5f9" }}>📋 Formações Mais Escaladas</h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={chartFormacoes} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis type="number" tick={{ fill: '#9ca3af', fontSize: 11 }} />
                      <YAxis type="category" dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} width={60} />
                      <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: 8, color: '#f1f5f9' }} />
                      <Bar dataKey="value" fill="#3b82f6" name="Rodadas">
                        <LabelList dataKey="value" position="right" fill="#e5e7eb" fontSize={11} />
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Top 5 Jogadores */}
                <div className="rounded-xl p-4" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
                  <h3 className="font-bold mb-3" style={{ color: "#f1f5f9" }}>🏆 Top 5 Jogadores Mais Escalados</h3>
                  <div className="space-y-2">
                    {data.top5.map((j: any, i: number) => (
                      <div key={j.nome} className="flex items-center gap-3 p-2 rounded-lg" style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(148, 163, 184, 0.1)" }}>
                        <span className="text-xl w-8 text-center">{MEDAL[i]}</span>
                        <div className="flex-1">
                          <div className="font-semibold text-sm" style={{ color: "#f1f5f9" }}>{j.nome}</div>
                          <div className="text-xs" style={{ color: "#94a3b8" }}>{j.escalacoes} escalações</div>
                        </div>
                        <div className="font-bold" style={{ color: "#34d399" }}>{j.pontos.toFixed(1)} pts</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Results Table */}
              <div className="rounded-xl p-4" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
                <h3 className="font-bold mb-3" style={{ color: "#f1f5f9" }}>📋 Resultados por Rodada</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr style={{ borderBottom: "1px solid rgba(148, 163, 184, 0.2)" }}>
                        <th className="py-2 px-2 text-left text-xs" style={{ color: "#94a3b8" }}>Rod</th>
                        <th className="py-2 px-2 text-right text-xs" style={{ color: "#94a3b8" }}>Escalado</th>
                        <th className="py-2 px-2 text-right text-xs" style={{ color: "#94a3b8" }}>Previsto</th>
                        <th className="py-2 px-2 text-right text-xs" style={{ color: "#94a3b8" }}>Ideal</th>
                        <th className="py-2 px-2 text-right text-xs" style={{ color: "#94a3b8" }}>Aprov.</th>
                        <th className="py-2 px-2 text-center text-xs" style={{ color: "#94a3b8" }}>Acertos</th>
                        <th className="py-2 px-2 text-left text-xs" style={{ color: "#94a3b8" }}>Capitão</th>
                        <th className="py-2 px-2 text-left text-xs" style={{ color: "#94a3b8" }}>Cap. Ideal</th>
                        <th className="py-2 px-2 text-center text-xs" style={{ color: "#94a3b8" }}>Cap OK</th>
                        <th className="py-2 px-2 text-left text-xs" style={{ color: "#94a3b8" }}>Formação</th>
                        <th className="py-2 px-2 text-right text-xs" style={{ color: "#94a3b8" }}>Custo</th>
                      </tr>
                    </thead>
                    <tbody>
                      {resultados.map((r: any) => {
                        const isExpanded = expandedRodada === r.rodada;
                        return (
                          <RodadaRow key={r.rodada} r={r} isExpanded={isExpanded} onToggle={() => setExpandedRodada(isExpanded ? null : r.rodada)} />
                        );
                      })}
                    </tbody>
                    <tfoot>
                      <tr style={{ borderTop: "2px solid rgba(148, 163, 184, 0.3)" }}>
                        <td className="py-2 px-2 font-bold" style={{ color: "#f1f5f9" }}>Total</td>
                        <td className="py-2 px-2 text-right font-bold" style={{ color: "#34d399" }}>{data.total_pontos_reais.toFixed(1)}</td>
                        <td className="py-2 px-2 text-right font-bold" style={{ color: "#54b4f7" }}>{data.total_pontos_esperada.toFixed(1)}</td>
                        <td className="py-2 px-2 text-right font-bold" style={{ color: "#eab308" }}>{data.total_pontos_ideal.toFixed(1)}</td>
                        <td className="py-2 px-2 text-right font-bold" style={{ color: "#06b6d4" }}>{data.aproveitamento_total.toFixed(1)}%</td>
                        <td className="py-2 px-2 text-center" style={{ color: "#94a3b8" }}>—</td>
                        <td className="py-2 px-2" style={{ color: "#94a3b8" }}>—</td>
                        <td className="py-2 px-2" style={{ color: "#94a3b8" }}>—</td>
                        <td className="py-2 px-2 text-center" style={{ color: "#f1f5f9" }}>{data.capitaes_ok}/{data.total_rodadas}</td>
                        <td className="py-2 px-2" style={{ color: "#94a3b8" }}>—</td>
                        <td className="py-2 px-2 text-right" style={{ color: "#94a3b8" }}>—</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>
            </>
          )}
        </TabsContent>

        {/* ===== SINGLE ROUND TAB ===== */}
        <TabsContent value="rodada" className="space-y-4">
          <div className="rounded-xl p-4" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
              <Select value={String(ano)} onValueChange={(v) => { setSelectedAno(Number(v)); setSelectedRodada(null); }}>
                <SelectTrigger style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(148, 163, 184, 0.2)", color: "#f1f5f9" }}>
                  <SelectValue placeholder="Ano" />
                </SelectTrigger>
                <SelectContent>
                  {anos.map((a) => <SelectItem key={a} value={String(a)}>{a}</SelectItem>)}
                </SelectContent>
              </Select>
              <Select value={String(rodada || "")} onValueChange={(v) => setSelectedRodada(Number(v))}>
                <SelectTrigger style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(148, 163, 184, 0.2)", color: "#f1f5f9" }}>
                  <SelectValue placeholder="Rodada" />
                </SelectTrigger>
                <SelectContent>
                  {rodadasDoAno.map((r: any) => (
                    <SelectItem key={r.rodada} value={String(r.rodada)}>Rodada {r.rodada} ({r.total_jogadores} jog.)</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {!formacaoAutomatica && (
                <Select value={formacao} onValueChange={setFormacao}>
                  <SelectTrigger style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(148, 163, 184, 0.2)", color: "#f1f5f9" }}>
                    <SelectValue placeholder="Formação" />
                  </SelectTrigger>
                  <SelectContent>
                    {FORMACOES.map((f) => <SelectItem key={f} value={f}>{f}</SelectItem>)}
                  </SelectContent>
                </Select>
              )}
              <Input type="number" value={orcamento} onChange={(e) => setOrcamento(Number(e.target.value) || 100)}
                placeholder="Orçamento" className="text-center"
                style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(148, 163, 184, 0.2)", color: "#f1f5f9" }} />
              <Button onClick={() => rodada && simularRodada.mutate({ rodada, ano, formacao, orcamento, formacaoAutomatica })}
                disabled={!rodada || simularRodada.isPending}
                style={{ background: "#54b4f7", color: "#000", fontWeight: 700 }}>
                {simularRodada.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : "▶ "}
                Simular Escalação
              </Button>
            </div>
            <div className="flex flex-wrap gap-4 mt-3 pt-3" style={{ borderTop: "1px solid rgba(148, 163, 184, 0.1)" }}>
              <label className="flex items-center gap-2 cursor-pointer text-sm" style={{ color: "#cbd5e1" }}>
                <input type="checkbox" checked={formacaoAutomatica} onChange={(e) => setFormacaoAutomatica(e.target.checked)}
                  className="rounded h-4 w-4 accent-blue-500" />
                Formação Automática (Melhor)
              </label>
            </div>
          </div>

          {simularRodada.error && (
            <div className="rounded-xl p-4" style={{ background: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.3)" }}>
              <p style={{ color: "#f87171" }}>Erro: {simularRodada.error.message}</p>
            </div>
          )}

          {simularRodada.data && (
            <div className="rounded-xl p-4 space-y-4" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(84, 180, 247, 0.3)" }}>
              <p className="font-bold text-lg" style={{ color: "#f1f5f9" }}>🔬 Resultado — R{rodada}/{ano}</p>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                <SimStat label="Formação" value={simularRodada.data.formacao} color="#f1f5f9" />
                <SimStat label="Pts Esperada" value={simularRodada.data.pontuacao_esperada?.toFixed(1)} color="#54b4f7" />
                <SimStat label="Pts Reais" value={(simularRodada.data as any).pontos_reais_total?.toFixed(1)} color="#34d399" />
                <SimStat label="Custo Total" value={`C$ ${simularRodada.data.custo_total?.toFixed(2)}`} color="#FFC107" />
                <SimStat label="Capitão" value={simularRodada.data.capitao?.apelido || "—"} color="#f1f5f9" />
              </div>
              {simularRodada.data.titulares && (
                <div className="rounded-xl overflow-hidden" style={{ border: "1px solid rgba(148, 163, 184, 0.1)" }}>
                  <table className="w-full text-sm">
                    <thead>
                      <tr style={{ borderBottom: "1px solid rgba(148, 163, 184, 0.15)", background: "rgba(30, 41, 59, 0.3)" }}>
                        <th className="text-left py-2 px-3" style={{ color: "#94a3b8" }}>Jogador</th>
                        <th className="text-center py-2 px-2" style={{ color: "#94a3b8" }}>Pos</th>
                        <th className="text-left py-2 px-2" style={{ color: "#94a3b8" }}>Clube</th>
                        <th className="text-right py-2 px-2" style={{ color: "#94a3b8" }}>Score</th>
                        <th className="text-right py-2 px-2" style={{ color: "#94a3b8" }}>Pts Reais</th>
                        <th className="text-right py-2 px-2" style={{ color: "#94a3b8" }}>Preço</th>
                        <th className="text-center py-2 px-2" style={{ color: "#94a3b8" }}>Papel</th>
                      </tr>
                    </thead>
                    <tbody>
                      {simularRodada.data.titulares.map((j: any) => (
                        <tr key={j.atleta_id} className="cursor-pointer"
                          onClick={() => setLocation(`/jogador/${j.atleta_id}`)}
                          style={{ borderBottom: "1px solid rgba(148, 163, 184, 0.08)" }}
                          onMouseEnter={(e) => e.currentTarget.style.background = "rgba(84, 180, 247, 0.05)"}
                          onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}>
                          <td className="py-2 px-3 font-bold" style={{ color: "#f1f5f9" }}>{j.apelido}</td>
                          <td className="py-2 px-2 text-center">
                            <span className="text-xs font-bold px-2 py-0.5 rounded" style={{ background: "rgba(148, 163, 184, 0.1)", color: "#94a3b8" }}>
                              {j.posicao || POSICOES[j.pos_id] || "?"}
                            </span>
                          </td>
                          <td className="py-2 px-2"><ClubeBadge clubeId={j.clube_id} size={16} showName={false} /></td>
                          <td className="py-2 px-2 text-right font-semibold" style={{ color: "#54b4f7" }}>{j.pontuacao_esperada?.toFixed(1)}</td>
                          <td className="py-2 px-2 text-right font-bold" style={{ color: (j.pontos_reais || 0) >= 0 ? "#34d399" : "#f87171" }}>
                            {j.pontos_reais?.toFixed(1) ?? "—"}
                          </td>
                          <td className="py-2 px-2 text-right" style={{ color: "#4da8f0" }}>C$ {j.preco?.toFixed(2)}</td>
                          <td className="py-2 px-2 text-center">
                            {simularRodada.data!.capitao?.atleta_id === j.atleta_id && (
                              <span className="text-xs font-bold px-2 py-0.5 rounded" style={{ background: "rgba(234, 179, 8, 0.15)", color: "#EAB308" }}>CAP</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

function MetricCard({ label, value, sub, color }: { label: string; value: string; sub: string; color: string }) {
  return (
    <div className="rounded-xl p-3 text-center" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
      <div className="text-xs uppercase tracking-wider" style={{ color: "#94a3b8" }}>{label}</div>
      <div className="text-2xl font-bold mt-1" style={{ color }}>{value}</div>
      <div className="text-xs mt-0.5" style={{ color: "#64748b" }}>{sub}</div>
    </div>
  );
}

function SimStat({ label, value, color }: { label: string; value: string | undefined; color: string }) {
  return (
    <div className="rounded-lg p-3 text-center" style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(148, 163, 184, 0.1)" }}>
      <div className="text-xs uppercase" style={{ color: "#94a3b8" }}>{label}</div>
      <div className="text-lg font-bold mt-1" style={{ color }}>{value || "—"}</div>
    </div>
  );
}

function RodadaRow({ r, isExpanded, onToggle }: { r: any; isExpanded: boolean; onToggle: () => void }) {
  return (
    <>
      <tr className="cursor-pointer" onClick={onToggle}
        style={{ borderBottom: "1px solid rgba(148, 163, 184, 0.08)" }}
        onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255, 255, 255, 0.03)"}
        onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}>
        <td className="py-2 px-2 font-semibold" style={{ color: "#f1f5f9" }}>
          <span className="mr-1">{isExpanded ? '▼' : '▶'}</span>R{r.rodada}
        </td>
        <td className="py-2 px-2 text-right font-semibold" style={{ color: r.pontos_reais >= 0 ? '#34d399' : '#f87171' }}>
          {r.pontos_reais.toFixed(1)}
        </td>
        <td className="py-2 px-2 text-right" style={{ color: "#54b4f7" }}>{r.pts_previsto.toFixed(1)}</td>
        <td className="py-2 px-2 text-right" style={{ color: "#eab308" }}>{r.pts_ideal.toFixed(1)}</td>
        <td className="py-2 px-2 text-right" style={{ color: r.aproveitamento >= 70 ? '#34d399' : r.aproveitamento >= 50 ? '#eab308' : '#f87171' }}>
          {r.aproveitamento.toFixed(1)}%
        </td>
        <td className="py-2 px-2 text-center" style={{ color: "#f1f5f9" }}>{r.acertos}/12</td>
        <td className="py-2 px-2 text-sm" style={{ color: "#cbd5e1" }}>{r.capitao}</td>
        <td className="py-2 px-2 text-sm" style={{ color: "#cbd5e1" }}>{r.capitao_ideal}</td>
        <td className="py-2 px-2 text-center">{r.cap_ok ? '✅' : '❌'}</td>
        <td className="py-2 px-2 text-sm" style={{ color: "#cbd5e1" }}>{r.formacao}</td>
        <td className="py-2 px-2 text-right text-sm" style={{ color: "#94a3b8" }}>C$ {r.custo_total.toFixed(1)}</td>
      </tr>
      {isExpanded && (
        <tr>
          <td colSpan={11} className="p-0">
            <RodadaDetails r={r} />
          </td>
        </tr>
      )}
    </>
  );
}

function RodadaDetails({ r }: { r: any }) {
  const POS_ORDER = ['GOL', 'LAT', 'ZAG', 'MEI', 'ATA', 'TEC'];

  const titularesByPos = useMemo(() => {
    const grouped: Record<string, any[]> = {};
    for (const t of r.titulares || []) {
      const pos = t.posicao || 'N/A';
      if (!grouped[pos]) grouped[pos] = [];
      grouped[pos].push(t);
    }
    return grouped;
  }, [r.titulares]);

  const melhoresByPos = useMemo(() => {
    const grouped: Record<string, any[]> = {};
    for (const m of r.melhores || []) {
      const pos = m.posicao || 'N/A';
      if (!grouped[pos]) grouped[pos] = [];
      grouped[pos].push(m);
    }
    return grouped;
  }, [r.melhores]);

  return (
    <div className="p-4" style={{ background: "rgba(30, 41, 59, 0.3)", borderTop: "1px solid rgba(148, 163, 184, 0.1)" }}>
      <div className="grid md:grid-cols-2 gap-6">
        {/* Left: Escalação Sugerida */}
        <div>
          <h4 className="font-bold text-sm mb-3" style={{ color: "#54b4f7" }}>🤖 Escalação Sugerida</h4>
          <div className="grid grid-cols-3 gap-2 mb-3 text-xs">
            <div className="rounded p-2 text-center" style={{ background: "rgba(15, 23, 42, 0.5)" }}>
              <div style={{ color: "#94a3b8" }}>Prevista</div>
              <div className="font-bold" style={{ color: "#54b4f7" }}>{r.pts_previsto.toFixed(1)}</div>
            </div>
            <div className="rounded p-2 text-center" style={{ background: "rgba(15, 23, 42, 0.5)" }}>
              <div style={{ color: "#94a3b8" }}>Real</div>
              <div className="font-bold" style={{ color: r.pontos_reais >= 0 ? '#34d399' : '#f87171' }}>{r.pontos_reais.toFixed(1)}</div>
            </div>
            <div className="rounded p-2 text-center" style={{ background: "rgba(15, 23, 42, 0.5)" }}>
              <div style={{ color: "#94a3b8" }}>Custo</div>
              <div className="font-bold" style={{ color: "#f1f5f9" }}>C$ {r.custo_total.toFixed(1)}</div>
            </div>
          </div>
          {POS_ORDER.map(pos => {
            const players = titularesByPos[pos];
            if (!players || players.length === 0) return null;
            return (
              <div key={pos} className="mb-2">
                <div className="text-xs font-semibold mb-1" style={{ color: POS_COLORS[pos] }}>{pos}</div>
                {players.map((p: any) => {
                  const isCap = p.apelido === r.capitao;
                  return (
                    <div key={p.atleta_id} className="flex items-center justify-between text-xs py-0.5 px-2 rounded"
                      style={{ background: isCap ? "rgba(234, 179, 8, 0.08)" : "transparent" }}>
                      <span style={{ color: "#f1f5f9", fontWeight: isCap ? 700 : 400 }}>
                        {p.apelido} {isCap ? '©' : ''}
                      </span>
                      <span className="flex gap-3">
                        <span style={{ color: "#94a3b8" }}>C$ {p.preco.toFixed(1)}</span>
                        <span style={{ color: p.pontos_reais >= 0 ? '#34d399' : '#f87171' }}>{p.pontos_reais.toFixed(1)}</span>
                      </span>
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>

        {/* Right: Melhor Time Possível */}
        <div>
          <h4 className="font-bold text-sm mb-3" style={{ color: "#eab308" }}>🏆 Melhor Time Possível</h4>
          <div className="grid grid-cols-2 gap-2 mb-3 text-xs">
            <div className="rounded p-2 text-center" style={{ background: "rgba(15, 23, 42, 0.5)" }}>
              <div style={{ color: "#94a3b8" }}>Pontuação</div>
              <div className="font-bold" style={{ color: "#eab308" }}>{r.pts_ideal.toFixed(1)}</div>
            </div>
            <div className="rounded p-2 text-center" style={{ background: "rgba(15, 23, 42, 0.5)" }}>
              <div style={{ color: "#94a3b8" }}>Acertos</div>
              <div className="font-bold" style={{ color: "#06b6d4" }}>{r.acertos}/12</div>
            </div>
          </div>
          {POS_ORDER.map(pos => {
            const players = melhoresByPos[pos];
            if (!players || players.length === 0) return null;
            return (
              <div key={pos} className="mb-2">
                <div className="text-xs font-semibold mb-1" style={{ color: POS_COLORS[pos] }}>{pos}</div>
                {players.map((p: any) => {
                  const isInEscalacao = r.titulares?.some((t: any) => t.atleta_id === p.atleta_id);
                  return (
                    <div key={p.atleta_id} className="flex items-center justify-between text-xs py-0.5 px-2 rounded"
                      style={{ background: isInEscalacao ? "rgba(34, 197, 94, 0.08)" : "transparent" }}>
                      <span style={{ color: "#f1f5f9" }}>
                        {isInEscalacao ? '✅ ' : ''}{p.apelido}
                      </span>
                      <span className="flex gap-3">
                        <span style={{ color: "#94a3b8" }}>C$ {p.preco.toFixed(1)}</span>
                        <span style={{ color: "#eab308" }}>{p.pontos.toFixed(1)}</span>
                      </span>
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
