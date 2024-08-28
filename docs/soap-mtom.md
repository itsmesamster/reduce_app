# MTOM/XOP optimization of binary data
https://www.ibm.com/docs/en/cics-ts/5.3?topic=infrastructure-support-mtomxop-optimization-binary-data
https://www.ibm.com/docs/en/cics-ts/5.3?topic=data-mtomxop-soap

In standard SOAP messages, binary objects are base64-encoded and included in the message body, which increases their size by 33%. For very large binary objects, this size increase can significantly impact transmission time. Implementing MTOM/XOP provides a solution to this problem.

The SOAP Message Transmission Optimization Mechanism (MTOM) and XML-binary Optimized Packaging (XOP) specifications, often referred to as MTOM/XOP, define a method for optimizing the transmission of large base64Binary data objects within SOAP messages.

# The MIME Multipart/Related Content-type
https://www.rfc-editor.org/rfc/rfc2387
```
'Content-Type': 'multipart/related; type="application/xop+xml"; boundary="uuid:492093f8-c22e-46fb-8995-0158d253b017"; start="<root.message@cxf.apache.org>"; start-info="text/xml"'
```

Required parameters:       Media type/subtype.
                           Type
Optional parameters:       Start
                           Start-info

## The Media Type/Subtype
```
multipart/related
```
The Multipart/Related media type is intended for compound objects
consisting of several inter-related body parts.

## The Type Parameter
```
type="application/xop+xml";
```
The type parameter must be specified and its value is the MIME media
type of the "root" body part.

## The Boundary
```
boundary="uuid:492093f8-c22e-46fb-8995-0158d253b017"
```
The separator of the individual bodies.
The first body starts with `--` and the boundary value like `--uuid:...`.
The last body is closed by `--`, the boundary value and `--` like `--uuid:...--`

## The Content-Disposition Headers
https://www.rfc-editor.org/rfc/rfc1806

## The Start Parameter
```
start="<root.message@cxf.apache.org>";
```
The start parameter, if given, is the content-ID of the compound
object's "root".  If not present the "root" is the first body part in
the Multipart/Related entity.  The "root" is the element the
applications processes first.
