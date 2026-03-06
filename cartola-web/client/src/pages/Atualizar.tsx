import { trpc } from "@/lib/trpc";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Loader2, RefreshCw, CheckCircle, AlertCircle, Database, Play, Download } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

export default function Atualizar() {
  const { data: mercado, isLoading: loadingMercado, refetch: refetchMercado } = trpc.cartola.mercadoStatus.useQuery();
  const { data: dbStats, isLoading: loadingDb, refetch: refetchDb } = trpc.db.stats.useQuery();
  const { data: rodadas, isLoading: loadingRodadas, refetch: refetchRodadas } = trpc.db.rodadasProcessadas.useQuery();

  const atualizarRodada = trpc.estrategia.atualizarRodada.useMutation({
    onSuccess: (data: any) => {
      toast.success(`Rodada ${data.rodada} atualizada com sucesso! ${data.jogadores_atualizados} jogadores processados.`);
      refetchDb();
      refetchRodadas();
    },
    onError: (err: any) => {
      toast.error(`Erro ao atualizar: ${err.message}`);
    },
  });

  const loading = loadingMercado || loadingDb || loadingRodadas;

  const handleRefreshAll = () => {
    refetchMercado();
    refetchDb();
    refetchRodadas();
    toast.info("Dados atualizados!");
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight" style={{ fontFamily: "var(--font-heading)" }}>
            Atualizar Resultados
          </h1>
          <p className="text-muted-foreground mt-1">
            Processar rodadas finalizadas e atualizar pontuações reais
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={handleRefreshAll} className="gap-2">
          <RefreshCw className="h-4 w-4" /> Atualizar Dados
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center min-h-[40vh]">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : (
        <>
          {/* Status Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="glass-card p-5">
              <div className="flex items-start gap-3">
                <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                  <RefreshCw className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Status do Mercado</p>
                  <p className="font-semibold mt-1">
                    {mercado?.status_mercado === 1 ? (
                      <Badge className="bg-green-500/20 text-green-400">Aberto</Badge>
                    ) : mercado?.status_mercado === 2 ? (
                      <Badge className="bg-red-500/20 text-red-400">Fechado</Badge>
                    ) : (
                      <Badge variant="outline">Desconhecido</Badge>
                    )}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Rodada {mercado?.rodada_atual || "—"} | Temporada {mercado?.temporada || "—"}
                  </p>
                </div>
              </div>
            </div>

            <div className="glass-card p-5">
              <div className="flex items-start gap-3">
                <div className="h-10 w-10 rounded-lg bg-chart-2/10 flex items-center justify-center">
                  <Database className="h-5 w-5 text-chart-2" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Banco de Dados</p>
                  <p className="font-semibold mt-1">
                    {dbStats?.total_registros_historico?.toLocaleString("pt-BR")} registros
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {dbStats?.rodadas_processadas} rodadas | {dbStats?.escalacoes_salvas} escalações
                  </p>
                </div>
              </div>
            </div>

            <div className="glass-card p-5">
              <div className="flex items-start gap-3">
                <div className="h-10 w-10 rounded-lg bg-chart-3/10 flex items-center justify-center">
                  <CheckCircle className="h-5 w-5 text-chart-3" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Último Processamento</p>
                  <p className="font-semibold mt-1">{dbStats?.ultima_rodada || "Nenhum"}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {dbStats?.ultimo_processamento
                      ? new Date(dbStats.ultimo_processamento).toLocaleString("pt-BR")
                      : "—"}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Update Actions */}
          <Card className="bg-card border-border border-primary/20">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Play className="h-5 w-5 text-primary" />
                Processar Rodada Finalizada
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Busca as pontuações reais da API do Cartola FC para a última rodada finalizada,
                calcula substituições, valorização e atualiza o banco de dados.
              </p>
              <div className="flex gap-3">
                <Button
                  onClick={() => atualizarRodada.mutate()}
                  disabled={atualizarRodada.isPending}
                  className="gap-2"
                >
                  {atualizarRodada.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Download className="h-4 w-4" />
                  )}
                  Atualizar Última Rodada
                </Button>
              </div>

              {atualizarRodada.data && (
                <div className="glass-card p-4 mt-3">
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle className="h-4 w-4 text-green-400" />
                    <span className="font-medium text-green-400">Atualização concluída</span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                    <div>
                      <p className="text-xs text-muted-foreground">Rodada</p>
                      <p className="font-medium">{atualizarRodada.data.rodada}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Jogadores</p>
                      <p className="font-medium">{atualizarRodada.data.jogadores_atualizados}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Substituições</p>
                      <p className="font-medium">{atualizarRodada.data.substituicoes || 0}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Valorização</p>
                      <p className={`font-medium ${(atualizarRodada.data.valorizacao_total || 0) >= 0 ? "text-green-400" : "text-red-400"}`}>
                        C$ {(atualizarRodada.data.valorizacao_total || 0).toFixed(2)}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Note */}
          <div className="glass-card p-5">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-amber-400 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium">Processamento Automático</p>
                <p className="text-sm text-muted-foreground mt-1">
                  O processamento de rodadas finalizadas também é executado automaticamente pelo sistema no Streamlit Cloud.
                  Os dados são atualizados no banco Neon e refletidos aqui em tempo real.
                  Use o botão acima para forçar uma atualização manual quando necessário.
                </p>
              </div>
            </div>
          </div>

          {/* Processed Rounds */}
          {rodadas && rodadas.length > 0 && (
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <CheckCircle className="h-5 w-5 text-chart-3" />
                  Rodadas Processadas ({rodadas.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-muted-foreground font-medium">
                        <th className="text-left py-3 px-3">Rodada</th>
                        <th className="text-left py-3 px-2">Ano</th>
                        <th className="text-right py-3 px-2">Total Jogadores</th>
                        <th className="text-right py-3 px-2">Prováveis</th>
                        <th className="text-right py-3 px-3">Processado em</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rodadas.map((r: any) => (
                        <tr key={`${r.ano}-${r.rodada}`} className="border-b border-border/30 hover:bg-accent/20">
                          <td className="py-2.5 px-3 font-medium">R{r.rodada}</td>
                          <td className="py-2.5 px-2">{r.ano}</td>
                          <td className="py-2.5 px-2 text-right">{r.total_jogadores}</td>
                          <td className="py-2.5 px-2 text-right">{r.jogadores_provaveis}</td>
                          <td className="py-2.5 px-3 text-right text-muted-foreground">
                            {r.processado_em ? new Date(r.processado_em).toLocaleString("pt-BR") : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
