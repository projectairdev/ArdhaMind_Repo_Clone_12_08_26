import type { Request, Response } from "express";
import { readOnlyRejection } from "./read_only_policy.mjs";

export { readOnlyRejection };

export function rejectReadOnlyMutation(action: string) {
  return (_req: Request, res: Response) => res.status(410).json(readOnlyRejection(action));
}
