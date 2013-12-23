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
