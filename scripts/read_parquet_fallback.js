#!/usr/bin/env node
/* Read selected LILA BLACK Parquet files where native PyArrow is unavailable.
 * Input: one or more exact file paths. Output: a JSON array to stdout.
 */
'use strict';

const parquet = require('parquetjs-lite');
// Node 24 decodes INT64 values as BigInt. The upstream implementation uses
// unary-plus in this conversion, which throws on BigInt. Number is exact here:
// audited TIMESTAMP_MILLIS values are ~1.77e9 and safely representable.
const types = require('parquetjs-lite/lib/types');
types.PARQUET_LOGICAL_TYPES.TIMESTAMP_MILLIS.fromPrimitive = value => new Date(Number(value));

async function main() {
  const paths = process.argv.slice(2);
  if (!paths.length) throw new Error('Pass at least one Parquet file path.');
  const rows = [];
  for (const filePath of paths) {
    const reader = await parquet.ParquetReader.openFile(filePath);
    try {
      const cursor = reader.getCursor();
      for (let row; (row = await cursor.next());) {
        const event = Buffer.isBuffer(row.event) ? row.event : Buffer.from(row.event ?? '');
        rows.push({
          user_id: row.user_id,
          match_id: row.match_id,
          map_id: row.map_id,
          x: row.x,
          y: row.y,
          z: row.z,
          timestamp_ms: row.ts instanceof Date ? row.ts.getTime() : Number(row.ts),
          event_base64: event.toString('base64'),
          source_file: filePath,
        });
      }
    } finally {
      await reader.close();
    }
  }
  process.stdout.write(JSON.stringify(rows));
}

main().catch(error => {
  process.stderr.write(`${error.stack || error}\n`);
  process.exitCode = 1;
});
