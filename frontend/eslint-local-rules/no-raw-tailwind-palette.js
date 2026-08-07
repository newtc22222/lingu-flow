/**
 * Forbids raw Tailwind default-palette utility classes (bg-slate-900,
 * text-emerald-300, border-rose-500/50, etc.) anywhere in a Vue template
 * class attribute (static `class="..."` or dynamic `:class="{...}"` /
 * `:class="[...]"`). tokens.css already exposes an approved bridge
 * (bg-ink, text-phosphor, bg-amber, ...) via the Tailwind `@theme` block -
 * any of these raw palette classes bypasses that bridge.
 */

const PALETTE = [
  'slate',
  'gray',
  'zinc',
  'neutral',
  'stone',
  'red',
  'orange',
  'amber',
  'yellow',
  'lime',
  'green',
  'emerald',
  'teal',
  'cyan',
  'sky',
  'blue',
  'indigo',
  'violet',
  'purple',
  'fuchsia',
  'pink',
  'rose',
];
const PREFIXES = [
  'bg',
  'text',
  'border',
  'ring',
  'from',
  'via',
  'to',
  'divide',
  'outline',
  'fill',
  'stroke',
  'shadow',
  'accent',
  'caret',
  'decoration',
];
const CLASS_RE = new RegExp(`^(?:[a-z]+:)?(${PREFIXES.join('|')})-(${PALETTE.join('|')})-[0-9]+`);

function checkToken(token, node, context) {
  if (CLASS_RE.test(token)) {
    context.report({
      node,
      message: `Raw Tailwind palette class "${token}" is not allowed - use a token-backed utility from tokens.css (e.g. bg-ink, text-phosphor, bg-amber) instead.`,
    });
  }
}

export default {
  'no-raw-tailwind-palette': {
    meta: { type: 'problem', schema: [] },
    create(context) {
      return {
        VAttribute(node) {
          if (node.directive) return;
          if (node.key?.name !== 'class') return;
          const raw = node.value?.value;
          if (typeof raw !== 'string') return;
          for (const token of raw.split(/\s+/).filter(Boolean)) {
            checkToken(token, node, context);
          }
        },
        VExpressionContainer(node) {
          const expr = node.expression;
          if (!expr) return;
          const literals = [];
          if (expr.type === 'ObjectExpression') {
            for (const prop of expr.properties) {
              const key = prop.key;
              if (key?.type === 'Literal' && typeof key.value === 'string')
                literals.push(key.value);
              if (key?.type === 'Identifier') literals.push(key.name);
            }
          } else if (expr.type === 'ArrayExpression') {
            for (const el of expr.elements) {
              if (el?.type === 'Literal' && typeof el.value === 'string') literals.push(el.value);
            }
          }
          for (const lit of literals) {
            for (const token of lit.split(/\s+/).filter(Boolean)) {
              checkToken(token, node, context);
            }
          }
        },
      };
    },
  },
};
