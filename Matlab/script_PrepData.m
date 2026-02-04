% Script to prepare/format data for use in training ORACLE.
% Also used to make Figures S1-S21.
clear;

% upfront stuffs.
CaseList={'Basel'};
%i=[1:1];
plot_type='tim';

% Get all of the case data.
D=PreProcData(CaseList);

% Loop over all of the case data.
for k=1:length(D)
    
    % Get the case's catalogue.
    Lat=D(k).Lat'; Lon=D(k).Lon'; Dep=D(k).Dep';
    T=D(k).T'; M=D(k).M';
    m1b=D(k).Mc;
    dMb=D(k).dMb;
    %dMb=0.01;
    dMd=D(k).dMd;
    dtd=D(k).dtd;
    
    % Get the case's hydraulic information.
    t=D(k).t';
    v=D(k).v';
    V=D(k).V';
    P=D(k).P';
    
    % Error handle.
    v(abs(v)<(0.01*max(abs(v))))=0;
    
    % Dither the magnitudes.
    M=M+(dMd)*rand(size(T))-dMd/2;
    
    % Filter based on Mc.
    Im=M>=m1b;
    Lat=Lat(Im); Lon=Lon(Im); Dep=Dep(Im);
    T=T(Im); M=M(Im);
    
    % Dither the times.
    T=T+dtd*rand(size(T))/(24*3600)-(dtd/2)/(24*3600);
    [~,It]=sort(T);
    Lat=Lat(It); Lon=Lon(It); Dep=Dep(It);
    T=T(It); M=M(It);
    
    % Anchor to injection start time.
    Ts=D(k).T1;
    tc=t; t=minutes(t-Ts);
    Tc=T; T=minutes(T-Ts);
    
    % Anchor to injection stage location.
    % d
    
    % Get differential time data.
    dT=diff([0,T]);

    % Compute pressure rate.
    Pw=diff(P)./diff(t); % MPa/min.
    
    % Compute the hydraulic moment.
    Eh=cumsum(diff([0,V]).*P*1e6)*((2*30*1000)/(3*0.46)); % Nm.

    % Compute time since injection rate sign change.
    dTS=getTime(t,v);
    dVc=get_dVc(V);
    
    % Interpolate the other mark data.
    vm=interp1(t,v,T,'linear','extrap'); % Instantaneous injection rate (m³/min).
    Vm=interp1(t,V,T,'linear','extrap'); % Cumulative volume (m³).
    dVm=[Vm(1),diff(Vm)]; % Sequential volume change (m³).
    dTSm=interp1(t,dTS,T,'linear','extrap'); % Time since injection sign change (log10[min]).
    Moc=getMw(cumsum(getMo(M))); % Cumulative seismic moment (as an equivalent magntidue).
    Pm=interp1(t,P,T,'linear','extrap'); % Pressure (MPa).
    pm=interp1(t(1:end-1)+diff(t)/2,Pw,T,'linear','extrap'); % Pressure rate (MPa/min).
    dPm=diff([interp1(t,P,min(t),'linear','extrap'),Pm]); % Seqeuntial pressure change (MPa).
    Ehm=getMw(interp1(t,Eh,T,'linear','extrap')); % Cumulative hydraulic moment (as an equivalent earthquake).
    dEhm=getMw(diff(interp1(t,Eh,[min(t),T],'linear','extrap'))); % Sequential hydraulic moment change (as an equivalent magnitude).
    aRs=get_aRs(dT,10); % Smoothed Causal Seismicity Rate (events/min).
    % Radius/location
    % b-value
    
    
    % Error handling.
    dEhm(isnan(dEhm))=m1b;
    dEhm(imag(dEhm)~=0)=m1b;
    dEhm(dEhm<=m1b)=m1b;
    Pm(Pm<=0)=1e-10;
    %pm(pm<=0)=1e-10;
    %vm(vm==0)=1e-10;
    %dVm(dVm==0)=1e-10;
    
    % Prep the header data.
    Lh={'Magnitude of Completeness (M)','Start Time (min)','End Time (min)'};
    Dh=[m1b,t(1),t(end)];
    Oh=array2table(Dh,'VariableNames',Lh);
    
    % Prep the catalogue data.
    Lc={'Time (min)','Inter-event Time (log10[min])','Magnitude (M)','Instantaneous Injection Rate (log10[m3/min])','Sequential Volume Change (log10[m3])','Sign of Sequential Volume Change (-)','Time Since Injection Sign Change (log10[min])','Cumulative Volume (log10[m3])','Cumulative Moment (M)','Pressure (log10[MPa])','Instantaneous Pressure Rate (log10[MPa/min])','Sequential Pressure Change (log10[MPa])' 'Sign of Pressure Change (-)','Cumulative Hydraulic Moment (M)','Sequential Hydraulic Moment Change (M)','Smoothed Causal Seismicity Rate log10[1/min]'};
    Dc=[T', log10(dT'), M', log10(abs(vm')), log10(abs(dVm')), sign(dVm'), log10(dTSm'), log10(Vm'), Moc', log10(Pm'), log10(abs(pm')), log10(abs(dPm')), sign(dPm'), Ehm', dEhm', log10(aRs') ];
    Oc=array2table(Dc,'VariableNames',Lc);
    
    % Prep the injection data.
    Li={'Time (min)', 'Injection Rate (log10[m3/min])','Sequential Volume Change (log10[m3])','Sign of Injection Rate (-)','Time Since Injection Sign Change (log10[min])'};
    Di=[t', log10(abs(v')), log10(dVc'), sign(v'), log10(dTS')];
    Oi=array2table(Di,'VariableNames',Li);
    
    % Stuff data into the output csv format.
    filepartname=['/Users/rschultz/Desktop/papers/nTPP-IS/codes/recast-1.0.1/data/',D(k).Case,'/',D(k).Case];
    writetable(Oh,[filepartname,'_Hed.csv']);
    writetable(Oc,[filepartname,'_Cat.csv']);
    writetable(Oi,[filepartname,'_Inj.csv']);
    
    % Check if there is any zero dT values.
    sum(dT==0)
    [sum(isnan(dEhm)) sum(~isreal(dEhm))]
    [sum(isnan(Dc(:))) sum(isnan(Di(:)))]
    [length(M) length(D(end).M)]
end


% Plot.

% Fit the Weibull distribution.
%dT(~dT>0)=1e-10;
Pw=wblfit(dT);
scale=(Pw(1)^-Pw(2)); shape=Pw(2);

% and some other distributions.
Pl=lognfit(dT);
[Pg1,Pg2]=normfit(log10(dT));
x=10.^(log10(min(dT)):0.001:log10(max(dT)));

% Get the median and mean values of the Weibull distribution.
Wavg=scale^(-1/shape)*gamma(1+1/shape);
Wmdn=exp(log(log(2)/scale)/shape);

dTr=wblrnd( Pw(1),Pw(2),[1 length(dT)]);
%dTr=lognrnd(Pl(1),Pl(2),[1 length(dT)]);
%dTr=10.^(normrnd(Pg1,Pg2,[1 length(dT)]));

% Report these values.
%[scale, shape]
%-log10([Wavg, mean(dT)])
%-log10([Wmdn, median(dT)])

% Plot distribution of time differences.
n=2;
figure(1); clf;
subplot(321);
histogram(log10(dT),round(n*sqrt(length(dT))),'Normalization','count'); hold on;
histogram(log10(dTr),round(n*sqrt(length(dTr))),'Normalization','count');
%plot(log10(x),wblpdf(x,Pw(1),Pw(2)));
%plot(log10(x),lognpdf(x,Pl(2),Pl(1)));
%plot(log10(x),normpdf(log10(x),Pg1,Pg2));
plot(log10(median(dT))*[1 1],ylim(),'--b');
plot(log10(mean(dT))*[1 1],ylim(),':b');
xlabel('Interevent times (log_{10}[min])'); ylabel('Counts');
subplot(322);
histogram((dT),round(n*sqrt(length(dT))),'Normalization','pdf'); hold on;
%histogram((dTr),round(n*sqrt(length(dTr))),'Normalization','pdf');
plot((x),wblpdf(x,Pw(1),Pw(2)));
%plot((x),lognpdf(x,Pl(2),Pl(1)));
%plot((x),normpdf(log10(x),Pg1,Pg2));
plot((median(dT))*[1 1],ylim(),'--b');
%set(gca, 'XScale', 'log')
xlabel('Interevent times (min)'); ylabel('PDF');
set(gca, 'YScale', 'log')
subplot(323);
histogram(log10(abs(dVm)),round(n*sqrt(length(dVm))),'Normalization','count'); hold on;
plot(log10(median(abs(dVm)))*[1 1],ylim(),'--b');
plot(log10(mean(abs(dVm)))*[1 1],ylim(),':b');
xlabel('Interevent volumes (log_{10}[m^3])'); ylabel('Counts');
subplot(324);
histogram(abs(dVm),round(n*sqrt(length(dVm))),'Normalization','PDF'); hold on;
plot(median(abs(dVm))*[1 1],ylim(),'--b');
xlabel('Interevent volumes (log_{10}[m^3])'); ylabel('PDF');
set(gca, 'YScale', 'log')
subplot(3,2,[5 6]);
histogram(log10(abs(vm)),round(n*sqrt(length(vm))),'Normalization','count'); hold on;
plot(log10(median(abs(vm)))*[1 1],ylim(),'--b');
xlabel('Instantaneous rates (log_{10}[m^3/min])'); ylabel('Counts');

% Plot to QC catalogue data.
figure(2); clf;
if(strcmpi(plot_type,'time'))
    t=tc; T=Tc;
end
% Plotting magnitude (marks).
ax21=subplot(411);
plot(T,M,'or');
xlabel('Time (minutes)'); ylabel('Magnitude');
% Plotting injection rate (side info).
ax22=subplot(412);
plot(t,v,'-b');
xlabel('Time (minutes)'); ylabel('Injection Rate (m^3/min)');
% Plotting time since injection rate changes.
ax23=subplot(413);
plot(t,dTS,'-b');
xlabel('Time (minutes)'); ylabel('Time since injection rate changes (min)');
% Plotting seismicity rate estimates.
ax24=subplot(414);
semilogy(T,1./dT,'-xk'); hold on;
semilogy(T,exp(movmean(log(1./dT),5)),'-m');
semilogy(T,aRs,'-r');
xlabel('Time (minutes)'); ylabel('Seismicity Rate (events/min)');

% Plot to QC supplementary mark data.
figure(3); clf;
% Magnitude marks.
ax31=subplot(411);
plot(T,M,'or'); hold on;
f=0.95*(max(M)-m1b)/max(v);
plot(t,f*v+m1b,'-b');
xlabel('Time (minutes)'); ylabel('Magnitude');
% Volume marks.
ax32=subplot(412);
plot(T,Vm,'ob'); hold on;
plot(t,V, '-b');
xlabel('Time (minutes)'); ylabel('Cumulative Volume (m^3)');
% Pressure marks.
ax33=subplot(413);
plot(T,Pm,'og'); hold on;
plot(t,P, '-g');
xlabel('Time (minutes)'); ylabel('Pressure (MPa)');
% Moment marks.
ax34=subplot(414);
plot(T,Ehm, '-b'); hold on;
plot(T,real(dEhm),'ob');
plot(T,Moc, '-r');
plot(T,Moc-Ehm, '-k');
xlabel('Time (minutes)'); ylabel('Seismic/Hydraulic Moment (Mw)');

% Link up the axes.
linkaxes([ax21 ax22 ax23 ax24  ax31 ax32 ax33 ax34],'x');

% Fit the GR-MFD b-value, etc.
M2=D(end).M; M2(Im)=M;
[b,b_err,a,R2,~,Mgr,Ngr,ngr]=Bval(M2,m1b,dMb);
po=[-b,a];
Mgr_fit=[m1b, max(D(end).M)];
Ngr_fit=10.^polyval(po,Mgr_fit);

% Plot the GR-MFD.
GREY=[0.85,0.85,0.85];
figure(4); clf;
semilogy(Mgr, Ngr, 'o', 'Color', 'k'); hold on;
bar(Mgr,ngr, 'FaceColor', GREY);
semilogy(Mgr_fit, Ngr_fit, '-', 'Color', 'black');
xlim([min(Mgr)-dMb/2 max(Mgr)+dMb/2]); ylim([0.7 1.3*max(Ngr)]);
plot(m1b*[1 1],ylim,'--k');
xlabel('Magnitude'); ylabel('Count');

% Scatter plot of injection rate vs event rate.
figure(5); clf;
semilogy(vm,1./dT,'o'); hold on;
[~,I]=sort(vm);
x=10.^movmean(-log(dT(I)),10);
semilogy(vm(I),x,'-xr');
xlabel('Injection rate (m^3/min)');
ylabel('Seismicity Rate (events/min)');

% Supplementary figure plot.  A general overview of the case data.
figure(51); clf;
% MvT.
ax1=subplot(311);
plot(T,M,'or'); hold on;
f=0.95*(max(M)-m1b)/max(v);
plot(t,f*v+m1b,'-b');
xlabel('Time (minutes)'); ylabel('Magnitude');
% RvT.
ax2=subplot(312);
semilogy(T,1./dT,'-xk'); hold on;
semilogy(T,exp(movmean(log(1./dT),5)),'-m');
%semilogy(T,aRs,'-r');
plot(t,v,'-b');
xlabel('Time'); ylabel('Inverse Inter-Event Time (event/min)');
% The GR-MFD.
subplot(313);
semilogy(Mgr, Ngr, 'o', 'Color', 'k'); hold on;
bar(Mgr,ngr, 'FaceColor', GREY);
semilogy(Mgr_fit, Ngr_fit, '-', 'Color', 'black');
xlim([min(Mgr)-dMb/2 max(Mgr)+dMb/2]); ylim([0.7 1.3*max(Ngr)]);
plot(m1b*[1 1],ylim,'--k');
xlabel('Magnitude'); ylabel('Count');
linkaxes([ax1 ax2],'x');

%%%% SUBROUNTINES.

% Get the seismic moment from event magnitude.
function [Mo]=getMo(Mw)
  Mo=10.^(1.5*Mw+9.1); % Mw to Mo (Nm).
end

% Get the event magnitude from seismic moment.
function [Mw]=getMw(Mo)
  Mw=(log10(Mo)-9.1)/1.5; % Mo (Nm) to Mw.
end

% Get the time since stop or start.
function [O]=getTime(t,r)
  s=sign(abs(r));
  O=zeros(size(s));
  ts=NaN;
  ini_flag=0;
  for i=1:length(r)
      if(s(i)~=ini_flag)
          ts=t(i);
          O(i)=t(i)-ts;
      else
          if(isnan(ts))
              O(i)=0;
          else
              O(i)=t(i)-ts;
          end
      end
  end
end

% Get the averaged rate of seismicity.
function [aRs]=get_aRs(dT,n)
  aRs=-10*ones(size(dT));
  v=-10*ones(size([1 n]));
  for i=1:length(dT)
      v(n+1)=log10(1/dT(i));
      v(1)=[];
      aRs(i)=mean(v);
  end
  aRs=10.^aRs;
end

% Get the change in (positive) injected volume.
function [dVc]=get_dVc(V)
  dVc=diff([0,V]);
  dVc(dVc<0)=0;
end