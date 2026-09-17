import Lean
import Lean.Util.FoldConsts

/-!
Read-only axiom dependency inspection of an already compiled module.

This is a verifier program, not a theorem or a proof dependency. It deliberately
does not use imported precomputed axiom-extension metadata: it walks the loaded
constant types and bodies directly, with all private module data available.
-/

open Lean

namespace Jsp467Audit

structure Closure where
  seen : NameSet := {}
  axioms : NameSet := {}
  deriving Inhabited

partial def visit (env : Environment) (todo : List Name) (s : Closure) :
    Except String Closure := do
  match todo with
  | [] => return s
  | n :: rest =>
    if s.seen.contains n then
      visit env rest s
    else
      let some ci := env.checked.get.find? n
        | throw s!"Missing constant in loaded dependency closure: {n}"
      if ci.isUnsafe || ci.isPartial then
        throw s!"Unsafe or partial constant reachable from a theorem: {n}"
      let s := { s with seen := s.seen.insert n }
      let s := match ci with
        | .axiomInfo _ => { s with axioms := s.axioms.insert n }
        | _ => s
      let next := ci.getUsedConstantsAsSet.toArray.toList ++ rest
      visit env next s

def allowed (n : Name) : Bool :=
  n == `propext || n == `Classical.choice || n == `Quot.sound

def jsonNames (xs : Array Name) : Json :=
  Json.arr (xs.map fun n ↦ Json.str n.toString)

def auditOne (env : Environment) (name : Name) : IO Bool := do
  let some ci := env.checked.get.find? name
    | throw <| IO.userError s!"Requested theorem does not exist: {name}"
  match ci with
  | .thmInfo _ => pure ()
  | _ => throw <| IO.userError s!"Requested constant is not a theorem: {name}"
  let s ← match visit env [name] {} with
    | .ok s => pure s
    | .error msg => throw <| IO.userError msg
  let axs := s.axioms.toArray.qsort Name.lt
  let disallowed := axs.filter fun n ↦ !allowed n
  IO.println <| (Json.mkObj [
    ("theorem", toJson name.toString),
    ("visitedConstants", toJson s.seen.toArray.size),
    ("axioms", jsonNames axs),
    ("disallowedAxioms", jsonNames disallowed),
    ("onlyStandardAxioms", toJson disallowed.isEmpty),
    ("exactStandardSet", toJson (disallowed.isEmpty && axs.size == 3)),
    ("method", toJson "direct constant-body traversal; no axiom metadata lookup")
  ]).compress
  return disallowed.isEmpty

end Jsp467Audit

unsafe def main (args : List String) : IO UInt32 := do
  let module :: names := args
    | throw <| IO.userError "Usage: lean --run AxiomClosure.lean MODULE THEOREM..."
  if names.isEmpty then
    throw <| IO.userError "At least one theorem name is required"
  initSearchPath (← findSysroot)
  Lean.withImportModules #[{ module := module.toName }] {} fun env => do
    let mut ok := true
    for name in names do
      let passed ← Jsp467Audit.auditOne env name.toName
      ok := ok && passed
    return if ok then 0 else 1
