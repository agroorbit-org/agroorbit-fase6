# 7. Preparação para envio

O enunciado solicita um único `.zip` ou `.rar`, com documentos, códigos, datasets, capturas e vídeo ou link. O padrão de nome é `nomecompleto_rm_turma_fase6_atividade.zip`.

## Identificação

O integrante conhecido pelos projetos anteriores é **Samuel Ramos de Almeida - RM99134**. A turma e os outros integrantes ainda precisam ser confirmados pelo usuário. O enunciado exige uma equipe de **3 a 5 alunos**; nomes e RMs não são inventados.

Edite `entrega.json` com a lista completa e a turma. O link público do vídeo já está preenchido: [assistir à demonstração de 3min43s](https://raw.githubusercontent.com/agroorbit-org/agroorbit-fase6/main/output/video/agroorbit-fase6-demo.mp4). O arquivo MP4 também acompanha o pacote. Se a instituição restringir os serviços aceitos, a equipe pode publicar o mesmo vídeo em Drive ou YouTube e atualizar o link.

## Gerar o pacote

```bash
# Versão de preparação: inclui arquivo PENDENCIAS.txt se faltarem dados.
python3 scripts/package_delivery.py --draft

# Versão final: bloqueia pendências de equipe, turma ou vídeo.
python3 scripts/package_delivery.py
```

O empacotador inclui código-fonte, modelo exportado, dados, evidências, PDF, MP4, metadados, testes e `dist/` executável. Exclui `.git`, credenciais, dependências instaladas, ambientes virtuais, caches e execuções temporárias. Reabre o ZIP e verifica CRC antes de concluir.

## Checklist de conteúdo

- [x] Arquitetura e descrição dos componentes.
- [x] Simulador executável e descrição dos sensores.
- [x] Código de processamento e datasets Bronze/Silver/Gold.
- [x] Automação e exemplo de saída.
- [x] Dashboard e indicadores descritos.
- [x] Roteiro de demonstração.
- [x] Vídeo de 3 a 5 minutos e link direto para acesso público.
- [ ] Confirmar equipe completa de 3 a 5 integrantes e turma.
- [ ] Revisar o vídeo com a equipe; a narração utiliza voz sintetizada.
- [ ] Conferir o nome do arquivo final e enviar pela plataforma da disciplina.

Apenas preparar o arquivo não constitui submissão. Nenhum upload na plataforma acadêmica foi realizado automaticamente.
