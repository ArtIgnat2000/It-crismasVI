// Структурная валидация .sb3 официальным парсером Scratch.
const fs = require('fs');
const parser = require('scratch-parser');

const file = process.argv[2];
const buf = fs.readFileSync(file);

parser(buf, false, (err, res) => {
    if (err) {
        console.error('INVALID:', JSON.stringify(err).slice(0, 4000));
        process.exit(1);
    }
    const targets = res.targets || res;
    let costumes = 0, sounds = 0, blocks = 0;
    for (const t of targets) {
        costumes += (t.costumes || []).length;
        sounds += (t.sounds || []).length;
        blocks += Object.keys(t.blocks || {}).length;
    }
    console.log(`VALID: targets=${targets.length} costumes=${costumes} sounds=${sounds} blocks=${blocks}`);
});
