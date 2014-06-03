## 2.0.0

* Definitions
    * More accurate scoping rules
    * "refers to" as a definition indicator
    * When finding a defining term, highlight the *first* time that term appears in its defining paragraph (rather than the last)
    * Defining multiple definitions at once (e.g. "X and B mean")
    * Per-reg ignore lists
* Appendices
    * Better depth parsing for headers
    * Better depth parsing for paragraphs
    * Account for "notes"
    * Allow for "code" tags
* Interpretations
    * Interpretations referring to multiple sections
    * Allow for multiple interpretations for a single paragraph/section
* Citations
    * Only for existing paragraphs
* SxS
    * If the same section is referred multiple times by adjacent SxS headers, combine them
    * Instead of duplicating SxS content when multiple citations are in a header, make a one-to-many relation
* Versions
    * Compile regulations from notices
    * Low-level patching system for notice changes
    * Allow notices to be manually modified (i.e. a bit higher-level patching)
    * Allow notices to be split by date effective
    * Spaces are added consistently to notice XML

## 12/31/2013

* Better appendices
    * Catch headers like 'G-14A' and 'G-18(C)(3)'
    * Paragraph markers for both '(a)' and 'a.'
    * Place G-12(a) headers on the same level as G-12
* Add keyterms to interpretations in XML
* Add method to expand macros in XML
* Catch additional definitions (indicated by tags followed by "means")

## 12/17/2013

* Better appendices
    * Account for 'Part I'
    * Drop non-generated TOCs
    * Catch many paragraphs which should be headers
    * Take many paragraph markers into account when figuring depth
* Generate multiple sections when a range of sections is [Reserved]
* Allow for interpretations of multiple sections
* Catch interpretations of deep paragraphs without parents (e.g. 2(a)(1) even when there is no interpretation of 2(a))

## 12/03/2013

* Regtext parsing from the XML version of 12 CFR 1026’s re-issuance
    * resolves many issues about paragraph depth, such as italic-markers
    * resolves certain issues with emphasis formatting
* Simple appendices (“flat” appendices) from XML for 12 CFR 1005 and 1026
* Interpretations from XML for the above regs
* Additional types of citations, including
    * "Commentary to"
    * "Comment 7-1"
    * multiple comment paragraphs beginning with a dash ("12(a)(1)-1 through -8, 12(a)(2)-1 through -9, 55(b)(3)-3, and 55(d)-1 through -3")
* Added automated code-coverage metrics (Coveralls.io)
