type Content = { type: 'text' | 'schema' | 'vertex' | 'edge', content: string };

function parseContent(text: string): Content[] {
    const removePattern = /<<<[\s\S]*?>>>/g;
    const cleanedText = text.replace(removePattern, '');
    const regex = /---(\w+)_Start([\s\S]*?)---\1_End/g;
    const result: Content[] = [];

    let lastIndex = 0;
    let match: RegExpExecArray | null;

    while (match = regex.exec(cleanedText)) {
        if (match.index > lastIndex) {
            result.push({
                type: 'text',
                content: cleanedText.slice(lastIndex, match.index).trim()
            });
        }

        result.push({
            type: match[1].toLowerCase() as 'schema' | 'vertex' | 'edge',
            content: match[2].trim()
        });

        lastIndex = regex.lastIndex;
    }

    if (lastIndex < cleanedText.length) {
        result.push({
            type: 'text',
            content: cleanedText.slice(lastIndex).trim()
        });
    }

    return result.filter(item => item.content.length > 0);
}

export {
    parseContent
}