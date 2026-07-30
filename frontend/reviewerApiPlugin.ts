import type { IncomingMessage, ServerResponse } from "node:http";
import { promises as fs } from "node:fs";
import path from "node:path";

import type { Plugin } from "vite";

const projectRoot = path.resolve(import.meta.dirname, "..");
const queueRoot = path.join(projectRoot, "data", "question_bank", "review_queue");
const resultRoot = path.join(projectRoot, "data", "question_bank", "review_results");

function json(response: ServerResponse, status: number, payload: unknown) {
  response.statusCode = status;
  response.setHeader("Content-Type", "application/json; charset=utf-8");
  response.end(JSON.stringify(payload));
}

function safeJsonName(value: string) {
  const name = path.basename(value);
  return name === value && name.endsWith(".json") ? name : null;
}

async function readBody(request: IncomingMessage) {
  const chunks: Buffer[] = [];
  for await (const chunk of request) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  return JSON.parse(Buffer.concat(chunks).toString("utf8")) as unknown;
}

async function listBatches() {
  await fs.mkdir(queueRoot, { recursive: true });
  const names = (await fs.readdir(queueRoot))
    .filter((name) => name.endsWith(".json"))
    .sort();
  return Promise.all(
    names.map(async (name) => {
      const stat = await fs.stat(path.join(queueRoot, name));
      return { name, updated_at: stat.mtime.toISOString() };
    }),
  );
}

export function reviewerApiPlugin(): Plugin {
  return {
    name: "shiguang-reviewer-local-api",
    configureServer(server) {
      server.middlewares.use(async (request, response, next) => {
        if (!request.url?.startsWith("/review-api/")) {
          next();
          return;
        }
        try {
          const url = new URL(request.url, "http://127.0.0.1");
          if (request.method === "GET" && url.pathname === "/review-api/batches") {
            json(response, 200, { batches: await listBatches() });
            return;
          }
          if (request.method === "GET" && url.pathname === "/review-api/batch") {
            const name = safeJsonName(url.searchParams.get("name") ?? "");
            if (!name) {
              json(response, 400, { detail: "Invalid batch name" });
              return;
            }
            const content = await fs.readFile(path.join(queueRoot, name), "utf8");
            let result: unknown = null;
            try {
              result = JSON.parse(
                await fs.readFile(path.join(resultRoot, name), "utf8"),
              );
            } catch {
              // A batch may not have any saved review result yet.
            }
            json(response, 200, { name, payload: JSON.parse(content), result });
            return;
          }
          if (request.method === "PUT" && url.pathname === "/review-api/result") {
            const name = safeJsonName(url.searchParams.get("name") ?? "");
            if (!name) {
              json(response, 400, { detail: "Invalid result name" });
              return;
            }
            const payload = await readBody(request);
            await fs.mkdir(resultRoot, { recursive: true });
            const target = path.join(resultRoot, name);
            const temporary = `${target}.tmp`;
            await fs.writeFile(
              temporary,
              `${JSON.stringify(payload, null, 2)}\n`,
              "utf8",
            );
            await fs.rename(temporary, target);
            json(response, 200, { saved: true, path: target });
            return;
          }
          json(response, 404, { detail: "Not found" });
        } catch (error) {
          json(response, 500, {
            detail: error instanceof Error ? error.message : "Reviewer API failed",
          });
        }
      });
    },
  };
}
