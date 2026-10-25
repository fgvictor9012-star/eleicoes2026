# Observatório Eleitoral 2026 — GitHub Pages

Site estático **público** para acompanhar resultados presidenciais oficiais do TSE, com comparação entre turnos, mapa de UFs e tabelas.

## Como publicar (sem Docker)

1. Crie uma conta gratuita em https://github.com/signup e confirme o e-mail.
2. No GitHub, clique em **New repository**. Use o nome `eleicoes2026`, marque **Public** e clique **Create repository**.
3. Escolha **uploading an existing file**. Envie **os arquivos e pastas do conteúdo deste ZIP** (não a pasta contêiner) — é importante preservar `.github/workflows/atualizar.yml`. Pelo upload do navegador, arquivos ocultos/pastas com ponto podem exigir o GitHub Desktop ou o Git. Alternativamente, execute `git init`, `git add .`, `git commit -m "Portal inicial"`, `git branch -M main`, `git remote add origin https://github.com/SEU_USUARIO/eleicoes2026.git`, `git push -u origin main`.
4. Abra **Settings → Pages**. Em **Build and deployment**, escolha **Deploy from a branch**, `main`, pasta `/(root)`, **Save**.
5. Em **Settings → Actions → General → Workflow permissions**, selecione **Read and write permissions**, salve. (Essas permissões permitem gravar `data/results.json`.)
6. Abra **Actions → Atualizar resultados do TSE → Run workflow** para forçar a primeira consulta. Acompanhe o log. O agendamento roda a cada 5 minutos; o GitHub pode atrasar ou não executar uma janela.
7. Seu endereço será `https://SEU_USUARIO.github.io/eleicoes2026/`, compartilhável com amigos.

**Observação:** na opção de upload manual do GitHub pode ser necessário criar o arquivo oculto `.github/workflows/atualizar.yml` pela interface **Add file → Create new file**, digitando exatamente o caminho, e colar o conteúdo que está no ZIP. Sem esse arquivo, o portal abre mas não se atualiza automaticamente.

## Que resultados há nesta versão?

- ✅ Brasil (BR), 26 estados e DF, exterior **agregado** (ZZ), quando retornados pelo TSE; 1º e 2º turnos.
- ✅ Total de votos válidos dos candidatos, % calculado dentro de cada abrangência/turno; diferença de votos, pontos percentuais e crescimento.
- ✅ Atualização agendada de 5 em 5 minutos, com o instante da última **consulta**, contagem de falhas e reaproveitamento dos últimos dados válidos em falhas transitórias.
- ⚠️ Município e países individuais: **pendentes**, não são falsamente apresentados como disponíveis. Para ampliar, é necessário processar EA12 (municípios), códigos municipais e dados oficiais do exterior por país.
- ⚠️ O código extrator foi feito com base na estrutura EA20 divulgada, **mas ainda não foi testado contra respostas ao vivo**, porque o ambiente que gerou o ZIP não permite acesso direto ao host do TSE. Confira a aba Actions e o resultado publicado antes de divulgar números. Arquivos ausentes/erros ficam sinalizados como dados ausentes.
- ⚠️ 6257 e 6258 são os identificadores federais usados para cada turno; confira a configuração oficial `https://resultados.tse.jus.br/oficial/comum/config/ele-c.json` se os dados não chegarem.
- ⚠️ A soma dos votos dos candidatos só funciona se o EA20 retornar todos os candidatos do cargo sem duplicação. Para produção, valide contra a apuração do TSE.

## Limitações dos 5 minutos

A agenda GitHub Actions executa **no mínimo** de 5 em 5 minutos, mas **não oferece SLA** e pode atrasar nos picos. O site ainda recarrega a base no navegador a cada 5 minutos; o horário da consulta e da publicação não é garantia de atualização do TSE. Fluxo: TSE → workflow → commit JSON → GitHub Pages → visitante.

## Conferência e resolução de problemas

- `Actions` não aparece: arquivo `.github/workflows/atualizar.yml` ausente, ou Actions desabilitado.
- `git push` 403: habilitar Workflow permissions **Read and write**.
- `data/results.json` vazio: ver log do workflow; a coleta pode falhar por conexão, TSE indisponível, 404 ou divergência de esquema.
- Mapa gráfico sem aparecer: rede bloqueia GeoJSON de terceiros; os botões de todas as UFs permanecem disponíveis.
- Site 404: aguarde a primeira publicação e confirme `Settings → Pages`, branch `main`, pasta `/(root)`.

Fontes: https://www.tse.jus.br/eleicoes/informacoes-tecnicas-sobre-a-divulgacao-de-resultados e https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
