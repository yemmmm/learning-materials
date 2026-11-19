import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const RUNTIME = process.env.ONTO_PRESENTATION_RUNTIME || '/home/yangxiang/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const SKILL = process.env.ONTO_PRESENTATION_SKILL || '/home/yangxiang/.codex/plugins/cache/openai-primary-runtime/presentations/26.904.11930/skills/presentations';
process.env.RUNTIME_NODE_MODULES ||= path.join(RUNTIME, 'node/node_modules');
const { finalizePresentation } = await import(pathToFileURL(path.join(SKILL, 'container_tools/artifact_tool_utils.mjs')).href);
const referencePath = path.join(ROOT, 'deck/editorial.pdf');
const finalPath = path.resolve(ROOT, process.argv[2] || 'exports/ontology-agent-slides-v3.0.pptx');
await fs.mkdir(path.join(ROOT, 'exports'), { recursive: true });
const result = await finalizePresentation({
  explicitTotalSlideCount: 18,
  workspaceDir: ROOT,
  candidatePath: path.join(ROOT, '.build-v3/candidate.pptx'),
  finalPath,
  pythonExecutable: path.join(RUNTIME, 'python/bin/python'),
  integrityValidatorPath: path.join(SKILL, 'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath: path.join(SKILL, 'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs: ['--expected-slide-size-emu', '18288000,10287000', '--validate-bullet-geometry', '--validate-heading-fit'],
  requiredNativeTableOwnerSlides: [],
  fontPolicy: {
    basis: 'reference',
    families: ['Noto Sans CJK SC', 'Noto Serif CJK SC'],
    referencePath,
    referenceSha256: createHash('sha256').update(await fs.readFile(referencePath)).digest('hex'),
  },
  verifyArtifactToolImport: true,
  receiptPath: path.join(ROOT, '.build-v3', `${path.basename(finalPath)}.validation.json`),
});
console.log(JSON.stringify(result, null, 2));
