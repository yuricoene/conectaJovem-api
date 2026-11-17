export default {
    async fetch(request) {
        const url = new URL(request.url);
        if (url.searchParams.get('erro') === 'sim') {
            throw new Error('Erro de teste provocado de propósito');
        }
 // lê um valor guardado fora do código (variável de ambiente)
        const turma = process.env.NOME_DA_TURMA || 'turma ainda não configurada';

 // esta mensagem aparece nos logs da Vercel
        console.log('A função /api/ola foi chamada');

 // devolve a resposta em formato JSON
        return Response.json({
            mensagem: 'Olá! Esta resposta foi gerada por uma função na nuvem.',
            turma: turma,
            horario: new Date().toISOString(),
            
        });
    },
}
