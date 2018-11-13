/*

Ce fichier correspond à l'extraction des informations nécessaires au recalcul de la PPA et à celui de l'ACS

La table créée dans work.sortie a le format attendu par l'outil de transfert mis à disposition par la CPAM du Lot

 */

/*data work.PPA ;
set allstat.fr1_0818 allstat.fr1_0918 allstat.fr1_1018;
where mtppaver >0;run ;

proc sort data=work.PPA (keep=matricul nirmme nirmon dtdemppa droppa droppa1 dtcloppa mtppaver mtppave1 mtotmme3
                                        mtotmme2 mtotmme1 mtotmon1 mtotmon2 mtotmon3 mtotfoy1 mtotfoy2 mtotfoy3 );
        by matricul ;
run ;*/

data work.essai (keep=matricul nirmme nirmon dtdemppa droppa droppa1 dtcloppa mtppaver mtppave1 mtotmme3 mtotmme2
        mtotmme1 mtotmon1 mtotmon2 mtotmon3 mtotfoy1 mtotfoy2 mtotfoy3 panbenau);
        set allstat.fr1_1018 ;
where  mtppaver>0;
run;

/*data work.fusion (keep=matricul nirmme nirmon dtdemppa droppa droppa1 dtcloppa mtppaver mtppave1 mtotmme3
                                        mtotmme2 mtotmme1 mtotmon1 mtotmon2 mtotmon3 mtotfoy1 mtotfoy2 mtotfoy3 dtpmtrid dtpmtrir);
        ;
        merge basenat.pad (in=a)
        work.essai (in=b);
        by matricul ;
        if a*b = 1 then output ;
run ;*/



DATA work.essai2; /* rajouter des colonnes jusqu'à 13 */
  SET work.essai ;
  ARRAY valeur   COL_1 COL_2 COL_3 COL_4 COL_5 COL_6 COL_7 COL_8 COL_9 COL_10 COL_11 COL_12 COL_13;
  DO OVER valeur ;
    IF MISSING(valeur) THEN valeur = "" ;
  END ;
RUN ;

/* renommer les colonnes transposées   */
data work.nirtranspo3 ;
        set work.essai2;
        rename col_1 = nirenf1 ;
        rename col_2 = nirenf2 ;
        rename col_3 = nirenf3 ;
        rename col_4 = nirenf4 ;
        rename col_5 = nirenf5 ;
        rename col_6 = nirenf6 ;
        rename col_7 = nirenf7 ;
        rename col_8 = nirenf8 ;
        rename col_9 = nirenf9 ;
        rename col_10 = nirenf10 ;
        rename col_11 = nirenf11 ;
        rename col_12 = nirenf12 ;
        rename col_13 = nirenf13 ;
run ;

data work.essai3;
        set work.nirtranspo3;
        rownum=_n_;
        run;

/* classer les variables pour la sortie EXCEL*/
proc sql ;
create table work.sortie as select dtdemppa, droppa, droppa1, dtcloppa, mtppaver, mtotmme3, mtotmme2,
        mtotmme1, mtotmon1, mtotmon2, mtotmon3, mtotfoy1, mtotfoy2, mtotfoy3, panbenau, rownum
from work.essai3;
quit;
