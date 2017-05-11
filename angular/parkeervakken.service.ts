import 'rxjs/add/operator/catch';
import 'rxjs/add/operator/map';
import { Injectable } from '@angular/core';
import { Http } from '@angular/http';
import { Observable } from 'rxjs/Observable';
import { Wegdeel } from '../models/wegdeel';

@Injectable()
export class ParkeervakkenService {
  private API_ROOT = 'https://acc.map.data.amsterdam.nl/';
  private API_PATH = 'maps/predictiveparking';

  constructor(private http: Http) {}

  public getVakken(boundingBox: string): Observable<Parkeervak[]> {
    return this.http.get(`${this.API_ROOT}${this.API_PATH}?` +
        'REQUEST=Getfeature&' +
        'VERSION=1.1.0&' +
        'SERVICE=wfs&' +
        'TYPENAME=alle_parkeervakken&' +
        'srsName=EPSG:4326&' +
        'count=1500&' +
        'startindex=0&' +
        'outputformat=geojson&' +
        `bbox=${boundingBox}`)
      .map(this.parseResponse)
      .catch((error) => Observable.throw(error.toString()));
  }

  private parseResponse(response) {
    const json = response.json();
    return json ? json.features : [];
  }
}
