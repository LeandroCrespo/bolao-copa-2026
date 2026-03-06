import { trpc } from "@/lib/trpc";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, Radar, Database, Calendar, Trophy } from "lucide-react";

export default function StatusColeta() {
  const { data: status, isLoading } = trpc.db.statusColeta.useQuery();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight" style={{ fontFamily: "var(--font-heading)" }}>
          Status de Coleta
        </h1>
        <p className="text-muted-foreground mt-1">
          Monitoramento de coleta de competições paralelas (estaduais, Copa do Brasil, etc.)
        </p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center min-h-[40vh]">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : !status ? (
        <div className="glass-card p-8 text-center">
          <Radar className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground">Dados de coleta não disponíveis.</p>
        </div>
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="glass-card stat-glow p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Registros Paralelas</p>
                  <p className="text-2xl font-bold mt-1">{status.total_competicoes_paralelas.toLocaleString("pt-BR")}</p>
                </div>
                <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                  <Database className="h-5 w-5" />
                </div>
              </div>
            </div>
            <div className="glass-card stat-glow p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Registros Histórico</p>
                  <p className="text-2xl font-bold mt-1">{status.total_jogadores_historico.toLocaleString("pt-BR")}</p>
                </div>
                <div className="h-10 w-10 rounded-lg bg-chart-2/10 flex items-center justify-center text-chart-2">
                  <Database className="h-5 w-5" />
                </div>
              </div>
            </div>
            <div className="glass-card stat-glow p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Fixtures Coletados</p>
                  <p className="text-2xl font-bold mt-1">{status.total_fixtures.toLocaleString("pt-BR")}</p>
                </div>
                <div className="h-10 w-10 rounded-lg bg-chart-3/10 flex items-center justify-center text-chart-3">
                  <Calendar className="h-5 w-5" />
                </div>
              </div>
            </div>
          </div>

          {/* Competitions Breakdown */}
          {status.competicoes.length > 0 && (
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Trophy className="h-5 w-5 text-primary" />
                  Competições ({status.competicoes.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {status.competicoes.map((c) => (
                    <div key={c.competicao} className="glass-card p-4">
                      <div className="flex items-center justify-between mb-2">
                        <Badge variant="outline" className="text-xs">{c.competicao}</Badge>
                        <span className="text-sm font-bold">{c.total}</span>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Última: {c.ultima_data ? new Date(c.ultima_data).toLocaleDateString("pt-BR") : "—"}
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Recent Games */}
          {status.ultimos_jogos.length > 0 && (
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Calendar className="h-5 w-5 text-chart-2" />
                  Últimos Jogos Coletados
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border">
                        <th className="text-left py-3 px-3 text-muted-foreground font-medium">Fixture</th>
                        <th className="text-left py-3 px-2 text-muted-foreground font-medium">Competição</th>
                        <th className="text-left py-3 px-2 text-muted-foreground font-medium">Data</th>
                        <th className="text-right py-3 px-3 text-muted-foreground font-medium">Jogadores</th>
                      </tr>
                    </thead>
                    <tbody>
                      {status.ultimos_jogos.map((g) => (
                        <tr key={g.fixture_id} className="border-b border-border/30 hover:bg-accent/30">
                          <td className="py-2.5 px-3 font-mono text-xs">{g.fixture_id}</td>
                          <td className="py-2.5 px-2">
                            <Badge variant="outline" className="text-[10px]">{g.competicao}</Badge>
                          </td>
                          <td className="py-2.5 px-2">
                            {g.data_jogo ? new Date(g.data_jogo).toLocaleDateString("pt-BR") : "—"}
                          </td>
                          <td className="py-2.5 px-3 text-right font-medium">{g.total_jogadores}</td>
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
